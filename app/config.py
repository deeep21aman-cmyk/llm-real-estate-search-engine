import os

from dotenv import load_dotenv


load_dotenv()

BASE_API_URL = os.getenv(
    "BASE_API_URL",
    "https://realtordrc2stg.wpenginepowered.com/wp-json/wp/v2/property",
)
FEATURES_API_URL = os.getenv(
    "FEATURES_API_URL",
    "https://realtordrc2stg.wpenginepowered.com/wp-json/wp/v2/property-features",
)

DATABASE_URL = os.getenv("DATABASE_URL")
DB_NAME = os.getenv("DB_NAME", "realtordr")
DB_USER = os.getenv("DB_USER", "amandeep")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
DB_SSLMODE = os.getenv("DB_SSLMODE")

OPEN_AI_MODEL = os.getenv("OPEN_AI_MODEL", "gpt-4.1-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20"))

EMBEDDING_MODEL_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}
EXPECTED_EMBEDDING_DIMENSION = EMBEDDING_MODEL_DIMENSIONS.get(EMBEDDING_MODEL)

VECTOR_RESULTS_LIMIT = 10

PER_PAGE = 100
REQUEST_TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
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
    "unit",
    "near",
    "nearby",
    "around",
    "close",
    "by",
    "estate",
    "realty",
    "sale",
    "place",
}
