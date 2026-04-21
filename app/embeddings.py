import logging

from openai import APITimeoutError, OpenAI, OpenAIError
from pgvector import Vector

from app.config import EMBEDDING_MODEL, EXPECTED_EMBEDDING_DIMENSION, OPENAI_TIMEOUT_SECONDS
from app.openai_env import require_env
from app.service_errors import ConfigurationError, ExternalServiceError


logger = logging.getLogger(__name__)
client = OpenAI(api_key=require_env("OPENAI_API_KEY"), timeout=OPENAI_TIMEOUT_SECONDS)


def _validate_embedding_length(embedding):
    if EXPECTED_EMBEDDING_DIMENSION is None:
        raise ConfigurationError(
            f"Unsupported EMBEDDING_MODEL '{EMBEDDING_MODEL}' for dimension validation"
        )

    if len(embedding) != EXPECTED_EMBEDDING_DIMENSION:
        raise ConfigurationError(
            f"Embedding dimension mismatch: expected {EXPECTED_EMBEDDING_DIMENSION}, got {len(embedding)}"
        )


def to_vector(value):
    if value is None:
        return None
    return Vector(value)


def embed_chunks(chunks: list[dict]) -> list[list[float]]:
    if not chunks:
        return []

    text = [chunk["chunk_text"] for chunk in chunks]
    logger.info("Generating chunk embeddings with model %s for %s chunks", EMBEDDING_MODEL, len(text))

    try:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    except (APITimeoutError, OpenAIError) as exc:
        raise ExternalServiceError(f"Embedding generation failed: {exc}") from exc

    embeddings = [item.embedding for item in response.data]
    for embedding in embeddings:
        _validate_embedding_length(embedding)
    return embeddings


def get_embedding(text):
    logger.info("Generating query embedding with model %s", EMBEDDING_MODEL)

    try:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    except (APITimeoutError, OpenAIError) as exc:
        raise ExternalServiceError(f"Embedding generation failed: {exc}") from exc

    embedding = response.data[0].embedding
    _validate_embedding_length(embedding)
    return embedding
