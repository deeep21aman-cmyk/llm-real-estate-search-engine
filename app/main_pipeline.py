import logging
import sys
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.embeddings import get_embedding
from app.intent_parser import detect_intent, parse_user_query
from app.query_processing import normalize_keywords
from app.ranking_engine import rank_results
from app.result_display import display_results
from app.results_formatter import format_results
from app.search_repository import search_repo, vector_search_repo


logger = logging.getLogger(__name__)


def _add_results(unique_results, results, max_new=None):
    added = 0

    for row in results:
        if row[0] in unique_results:
            continue
        unique_results[row[0]] = row
        added += 1
        if max_new is not None and added >= max_new:
            break


def search_transcripts(query):
    try:
        from app.KNOWLEDGE.app.search import search_transcripts as knowledge_search
    except ImportError:
        logger.warning("Knowledge search module is unavailable")
        return {
            "answer": "Knowledge search is temporarily unavailable.",
            "sources": [],
        }

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

    related_properties = result.get("related_properties", [])
    if related_properties:
        print("\nRelated Properties:\n")
        for property_item in related_properties:
            title = property_item.get("title", "")
            price = property_item.get("price", "")
            bedrooms = property_item.get("bedrooms", "")
            bathrooms = property_item.get("bathrooms", "")
            address = property_item.get("address", "")
            link = property_item.get("link", "")

            print(f"- {title}")
            print(f"  Price: {price}")
            print(f"  Beds/Baths: {bedrooms}/{bathrooms}")
            print(f"  Address: {address}")
            if link:
                print(f"  Link: {link}")
            print()


def _format_related_property(row):
    return {
        "title": row[1],
        "price": row[2],
        "bedrooms": row[3],
        "bathrooms": row[4],
        "size": row[5],
        "address": row[6],
        "link": row[7],
    }


def get_related_properties_for_knowledge(query, limit=3):
    try:
        query_embedding = get_embedding(query)
        vector_results = vector_search_repo(query_embedding, limit=10)
        keywords = normalize_keywords(query.split())
        parsed = {
            "unknown_terms": keywords,
            "feature_names": [],
            "location": None,
            "location_keywords": [],
        }
        scored_results = rank_results(vector_results, query_embedding, parsed)
        top_results = [row for _, row in scored_results[:min(limit, 3)]]
        return [_format_related_property(row) for row in top_results]
    except Exception as exc:
        logger.warning("Related property suggestion lookup failed: %s", exc)
        return []


def run_property_search(query):
    total_start = time.time()
    MAX_RESULTS = 6
    TOTAL_RESULTS = 8
    SEARCH_STAGE_LIMIT = 24
    logger.info("Starting property search pipeline")

    parsed = parse_user_query(query)
    logger.info("Parsed query successfully")

    keywords = normalize_keywords(parsed["unknown_terms"])
    query_embedding = get_embedding(query)

    logger.info("Running structured repository search")
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
        limit=SEARCH_STAGE_LIMIT,
    )
    all_results = list(exact_results[:8])

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
        limit=SEARCH_STAGE_LIMIT,
    )

    all_results.extend(numeric_relaxed_results[:5])

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
        [],
        keywords,
        query_embedding,
        limit=SEARCH_STAGE_LIMIT,
    )

    all_results.extend(same_bedroom_results[:4])

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
        limit=SEARCH_STAGE_LIMIT,
    )

    all_results.extend(feature_results[:4])

    unique_results = {}
    _add_results(unique_results, all_results)

    logger.info("Running vector repository search")
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
        parsed["location"],
        limit=12,
    )

    _add_results(unique_results, vector_results)

    should_run_relaxed_vector = (
        len(unique_results) < TOTAL_RESULTS
        or bool(keywords)
        or bool(parsed["feature_names"])
    )

    if should_run_relaxed_vector:
        logger.info("Running relaxed vector fallback search")
        relaxed_vector_results = vector_search_repo(
            query_embedding,
            min_price=parsed["min_price"],
            max_price=parsed["max_price"],
            is_discounted=parsed["is_discounted"],
            location=parsed["location"],
            limit=16,
        )
        _add_results(unique_results, relaxed_vector_results)

    combined_results = list(unique_results.values())
    scored_results = rank_results(combined_results, query_embedding, parsed)
    top_results = [r for _, r in scored_results[:MAX_RESULTS]]
    additional = [r for _, r in scored_results[MAX_RESULTS:TOTAL_RESULTS]]

    formatted_results = format_results(parsed, keywords, top_results, additional)
    display_results(parsed, keywords, top_results, additional)

    logger.info("Final response prepared with %s top results", len(top_results))
    print(f"\nTotal pipeline time: {time.time() - total_start:.4f} seconds")

    return formatted_results


if __name__ == "__main__":
    query = "financing options"
    intent = detect_intent(query)

    if intent == "PROPERTY_SEARCH":
        print(run_property_search(query))
    elif intent == "KNOWLEDGE_SEARCH":
        knowledge_result = search_transcripts(query)
        knowledge_result["related_properties"] = get_related_properties_for_knowledge(query)
        display_knowledge_results(knowledge_result)
