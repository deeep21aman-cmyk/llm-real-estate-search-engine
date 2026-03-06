

BASE_API_URL = "https://realtordrc2stg.wpenginepowered.com/wp-json/wp/v2/property"
FEATURES_API_URL="https://realtordrc2stg.wpenginepowered.com/wp-json/wp/v2/property-features"

DB_NAME = "realtordr"
DB_USER = "amandeep"
DB_HOST = "localhost"
DB_PORT = 5432


OPEN_AI_MODEL="gpt-4.1-mini"
EMBEDDING_MODEL="text-embedding-3-small"

VECTOR_RESULTS_LIMIT=5

PER_PAGE = 100
REQUEST_TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
REQUEST_DELAY = 0.3

IGNORE_EXPLANATION_TERMS = {
    "house",
    "home",
    "property",
    "villa",
    "condo",
    "apartment",
    "listing",
    "residence",
    "unit"
}
