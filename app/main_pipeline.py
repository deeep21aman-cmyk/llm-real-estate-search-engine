from intent_parser import parse_user_query
from generate_embeddings import get_embedding
from search_repository import search_repo, vector_search_repo
from query_processing import normalize_keywords
from ranking_engine import rank_results
from result_display import display_results
from config import VECTOR_RESULTS_LIMIT

import time


query = input("What properties are you interested in ? ")

total_start = time.time()

# -----------------------
# Parse user query
# -----------------------
parsed = parse_user_query(query)

# -----------------------
# Normalize keywords
# -----------------------
keywords = normalize_keywords(parsed["unknown_terms"])

# -----------------------
# Embed query
# -----------------------
query_embedding = get_embedding(query)

# -----------------------
# Search repository
# -----------------------
search_results = search_repo(
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
)

# -----------------------
# Rank results
# -----------------------
scored_results = rank_results(search_results, query_embedding)

# -----------------------
# Select top results
# -----------------------
if len(scored_results) >= VECTOR_RESULTS_LIMIT:

    top_results = [r for _, r in scored_results[:VECTOR_RESULTS_LIMIT]]
    additional = []

else:

    needed = VECTOR_RESULTS_LIMIT - len(scored_results)

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

    existing_ids = {r[1][0] for r in scored_results}

    additional = []

    for r in vector_results:
        if r[0] not in existing_ids:
            additional.append(r)
        if len(additional) == needed:
            break

    top_results = [r for _, r in scored_results]


# -----------------------
# Display results
# -----------------------

display_results(parsed, keywords, top_results, additional)

print(f"\nTotal pipeline time: {time.time() - total_start:.4f} seconds")