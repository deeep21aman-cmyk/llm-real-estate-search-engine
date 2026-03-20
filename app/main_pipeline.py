from RealtorDR.app.intent_parser import detect_intent, parse_user_query
from RealtorDR.app.embeddings import get_embedding
from RealtorDR.app.search_repository import search_repo, vector_search_repo
from RealtorDR.app.query_processing import normalize_keywords
from RealtorDR.app.ranking_engine import rank_results
from RealtorDR.app.result_display import display_results
from RealtorDR.app.results_formatter import format_results

import time


def search_transcripts(query):
    from KNOWLEDGE.app.search import search_transcripts as knowledge_search

    return knowledge_search(query)


def display_knowledge_results(result):
    print("\nAnswer:\n")
    print(result.get("answer", ""))

    sources = result.get("sources", [])
    if sources:
        print("\nSources:\n")
        for source in sources:
            url = source.get("url")
            if url:
                print(f"- {url}")

def run_property_search(query):

    total_start = time.time()
    MAX_RESULTS = 6
    TOTAL_RESULTS = 8

    # -----------------------
    # Parse user query
    # -----------------------
    parsed = parse_user_query(query)
    print(parsed)

    # -----------------------
    # Normalize keywords
    # -----------------------
    keywords = normalize_keywords(parsed["unknown_terms"])

    # -----------------------
    # Embed query
    # -----------------------
    query_embedding = get_embedding(query)

    # -----------------------
    # Stage 1 — Exact match (all constraints)
    # -----------------------
    exact_results = search_repo(
        parsed["bedrooms"],
        parsed["bathrooms"],
        parsed["min_bathrooms"],
        parsed["max_bathrooms"],
        parsed["min_bedrooms"],
        parsed["max_bedrooms"],
        parsed["min_price"],
        parsed["max_price"],
        parsed["min_size"],
        parsed["max_size"],
        parsed["min_lot_size"],
        parsed["max_lot_size"],
        parsed["min_year_built"],
        parsed["max_year_built"],
        parsed["is_discounted"],
        parsed["min_down_payment_amount"],
        parsed["max_down_payment_amount"],
        parsed["min_down_payment_percent"],
        parsed["max_down_payment_percent"],
        parsed["location"],
        parsed["location_keywords"],
        parsed["feature_names"],
        keywords,
        query_embedding,
    )

    # Stage 1 can fill up to MAX_RESULTS
    exact_results = exact_results[:MAX_RESULTS]
    all_results = list(exact_results)

    # -----------------------
    # Stage 2 — Relax numeric constraints but keep features
    # -----------------------
    if parsed["bedrooms"]:
        relaxed_min_bed = parsed["bedrooms"] - 1
        relaxed_max_bed = parsed["bedrooms"] + 1
    else:
        relaxed_min_bed = parsed["min_bedrooms"]
        relaxed_max_bed = parsed["max_bedrooms"]

    numeric_relaxed_results = search_repo(
        None,
        parsed["bathrooms"],
        parsed["min_bathrooms"],
        parsed["max_bathrooms"],
        relaxed_min_bed,
        relaxed_max_bed,
        parsed["min_price"],
        parsed["max_price"],
        parsed["min_size"],
        parsed["max_size"],
        parsed["min_lot_size"],
        parsed["max_lot_size"],
        parsed["min_year_built"],
        parsed["max_year_built"],
        parsed["is_discounted"],
        parsed["min_down_payment_amount"],
        parsed["max_down_payment_amount"],
        parsed["min_down_payment_percent"],
        parsed["max_down_payment_percent"],
        parsed["location"],
        parsed["location_keywords"],
        parsed["feature_names"],
        keywords,
        query_embedding,
    )

    remaining = MAX_RESULTS - len(all_results)
    numeric_relaxed_results = numeric_relaxed_results[:min(2, remaining)]
    all_results.extend(numeric_relaxed_results)

    # -----------------------
    # Stage 3 — Same bedrooms but remove feature constraint
    # -----------------------
    same_bedroom_results = search_repo(
        parsed["bedrooms"],
        parsed["bathrooms"],
        parsed["min_bathrooms"],
        parsed["max_bathrooms"],
        parsed["min_bedrooms"],
        parsed["max_bedrooms"],
        parsed["min_price"],
        parsed["max_price"],
        parsed["min_size"],
        parsed["max_size"],
        parsed["min_lot_size"],
        parsed["max_lot_size"],
        parsed["min_year_built"],
        parsed["max_year_built"],
        parsed["is_discounted"],
        parsed["min_down_payment_amount"],
        parsed["max_down_payment_amount"],
        parsed["min_down_payment_percent"],
        parsed["max_down_payment_percent"],
        parsed["location"],
        parsed["location_keywords"],
        [],  # remove features
        keywords,
        query_embedding,
    )

    remaining = MAX_RESULTS - len(all_results)
    same_bedroom_results = same_bedroom_results[:min(2, remaining)]
    all_results.extend(same_bedroom_results)

    # -----------------------
    # Stage 4 — Feature focused search (any bedrooms)
    # -----------------------
    feature_results = search_repo(
        None,
        None,
        None,
        None,
        None,
        None,
        parsed["min_price"],
        parsed["max_price"],
        None,
        None,
        None,
        None,
        None,
        None,
        parsed["is_discounted"],
        None,
        None,
        None,
        None,
        parsed["location"],
        parsed["location_keywords"],
        parsed["feature_names"],
        keywords,
        query_embedding,
    )

    remaining = MAX_RESULTS - len(all_results)
    feature_results = feature_results[:min(2, remaining)]
    all_results.extend(feature_results)

    # -----------------------
    # Deduplicate results
    # -----------------------
    unique_results = {}
    for r in all_results:
        unique_results[r[0]] = r

    vector_results = vector_search_repo(
        query_embedding,
        parsed["bedrooms"],
        parsed["bathrooms"],
        parsed["min_bathrooms"],
        parsed["max_bathrooms"],
        parsed["min_bedrooms"],
        parsed["max_bedrooms"],
        parsed["min_price"],
        parsed["max_price"],
        parsed["min_size"],
        parsed["max_size"],
        parsed["min_lot_size"],
        parsed["max_lot_size"],
        parsed["min_year_built"],
        parsed["max_year_built"],
        parsed["is_discounted"],
    )

    for r in vector_results:
        unique_results[r[0]] = r

    combined_results = list(unique_results.values())

    scored_results = rank_results(combined_results, query_embedding, parsed)
    top_results = [r for _, r in scored_results[:MAX_RESULTS]]
    additional = [r for _, r in scored_results[MAX_RESULTS:TOTAL_RESULTS]]

    # -----------------------
    # Format results for API
    # -----------------------
    formatted_results = format_results(parsed, keywords, top_results, additional)

    # -----------------------
    # Display results (CLI)
    # -----------------------
    display_results(parsed, keywords, top_results, additional)

    print(f"\nTotal pipeline time: {time.time() - total_start:.4f} seconds")

    return formatted_results

if __name__ == "__main__":
    query='how safe is dominican'
    intent = detect_intent(query)

    if intent == "PROPERTY_SEARCH":
        print(run_property_search(query))
    elif intent == "KNOWLEDGE_SEARCH":
        display_knowledge_results(search_transcripts(query))
