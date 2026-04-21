import logging
import re

import psycopg
from pgvector.psycopg import register_vector

from app.config import (
    DATABASE_URL,
    DB_CONNECT_TIMEOUT,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_SSLMODE,
    DB_USER,
    EMBEDDING_MODEL,
    EXPECTED_EMBEDDING_DIMENSION,
)
from app.service_errors import ConfigurationError


logger = logging.getLogger(__name__)


def _is_remote_connection() -> bool:
    if DATABASE_URL:
        lowered = DATABASE_URL.lower()
        return "localhost" not in lowered and "127.0.0.1" not in lowered
    return DB_HOST not in {"localhost", "127.0.0.1"}


def _connection_kwargs():
    kwargs = {"connect_timeout": DB_CONNECT_TIMEOUT}

    if DATABASE_URL:
        kwargs["conninfo"] = DATABASE_URL
    else:
        kwargs.update(
            {
                "dbname": DB_NAME,
                "user": DB_USER,
                "password": DB_PASSWORD,
                "host": DB_HOST,
                "port": DB_PORT,
            }
        )

    sslmode = DB_SSLMODE
    if not sslmode and _is_remote_connection():
        sslmode = "require"
    if sslmode:
        kwargs["sslmode"] = sslmode

    return kwargs


def get_connection():
    conn = psycopg.connect(**_connection_kwargs())
    register_vector(conn)
    return conn


def validate_pgvector_schema():
    logger.info("Validating pgvector schema for embedding model %s", EMBEDDING_MODEL)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            has_vector_extension = cur.fetchone()[0]
            if not has_vector_extension:
                raise ConfigurationError("pgvector extension 'vector' is not installed")

            cur.execute(
                """
                SELECT format_type(a.atttypid, a.atttypmod)
                FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'properties'
                  AND a.attname = 'description_embedding'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
                ORDER BY n.nspname = 'public' DESC, n.nspname
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if row is None:
                raise ConfigurationError("properties.description_embedding column not found")

            format_type = row[0] or ""
            match = re.search(r"vector\((\d+)\)", format_type)
            if not match:
                raise ConfigurationError(
                    "properties.description_embedding must be defined as vector(n)"
                )

            actual_dimension = int(match.group(1))
            if EXPECTED_EMBEDDING_DIMENSION is None:
                raise ConfigurationError(
                    f"Unsupported EMBEDDING_MODEL '{EMBEDDING_MODEL}' for dimension validation"
                )

            if actual_dimension != EXPECTED_EMBEDDING_DIMENSION:
                raise ConfigurationError(
                    "Embedding dimension mismatch: "
                    f"model {EMBEDDING_MODEL} expects {EXPECTED_EMBEDDING_DIMENSION}, "
                    f"database column is {actual_dimension}"
                )

            logger.info(
                "pgvector schema validated successfully with dimension %s",
                actual_dimension,
            )


def upsert_features(features):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            for feature in features:
                cur.execute(
                    """
                    INSERT INTO features (id, name, slug, count)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        slug = EXCLUDED.slug,
                        count = EXCLUDED.count;
                    """,
                    (
                        feature["id"],
                        feature["name"],
                        feature["slug"],
                        feature["count"],
                    ),
                )
    conn.close()


def upsert_properties(properties):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            for prop in properties:
                cur.execute(
                    """
                    INSERT INTO properties (
                        slug, link, modified, status, is_active,
                        price, old_price, bedrooms, bathrooms,
                        size, lot_size, year_built,
                        latitude, longitude,
                        title, description, address
                    )
                    VALUES (%s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s, %s)
                    ON CONFLICT (slug)
                    DO UPDATE SET
                        link = EXCLUDED.link,
                        modified = EXCLUDED.modified,
                        status = EXCLUDED.status,
                        is_active = EXCLUDED.is_active,
                        price = EXCLUDED.price,
                        old_price = EXCLUDED.old_price,
                        bedrooms = EXCLUDED.bedrooms,
                        bathrooms = EXCLUDED.bathrooms,
                        size = EXCLUDED.size,
                        lot_size = EXCLUDED.lot_size,
                        year_built = EXCLUDED.year_built,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        address = EXCLUDED.address,
                        updated_at = NOW() RETURNING id;
                    """,
                    (
                        prop["slug"],
                        prop["link"],
                        prop["modified"],
                        prop["status"],
                        prop["is_active"],
                        prop["price"],
                        prop["old_price"],
                        prop["bedrooms"],
                        prop["bathrooms"],
                        prop["size"],
                        prop["lot_size"],
                        prop["year_built"],
                        prop["latitude"],
                        prop["longitude"],
                        prop["title"],
                        prop["description"],
                        prop["address"],
                    ),
                )
                row = cur.fetchone()
                property_id = row[0]
                cur.execute("DELETE FROM property_features WHERE property_id=%s", (property_id,))
                for feature in prop["feature_ids"]:
                    cur.execute(
                        """
                        INSERT INTO property_features(property_id,feature_id) VALUES (%s,%s)
                        """,
                        (property_id, feature),
                    )

    conn.close()
