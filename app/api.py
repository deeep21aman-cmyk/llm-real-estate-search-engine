import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from psycopg import Error as PsycopgError
from pydantic import BaseModel

from app.db import validate_pgvector_schema
from app.main_pipeline import (
    get_related_properties_for_knowledge,
    run_property_search,
    search_transcripts,
)
from app.intent_parser import detect_intent
from app.service_errors import ConfigurationError, ExternalServiceError


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class Query(BaseModel):
    query: str


@app.on_event("startup")
def validate_startup():
    validate_pgvector_schema()


@app.post("/chat")
def chat(req: Query):
    logger.info("Received /chat request")
    try:
        query = req.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        intent = detect_intent(query)

        if intent == "PROPERTY_SEARCH":
            property_response = run_property_search(query)
            logger.info("Returning property search response")
            return {
                "type": "property",
                **property_response,
            }

        if intent == "KNOWLEDGE_SEARCH":
            knowledge_response = search_transcripts(query)
            related_properties = get_related_properties_for_knowledge(query, limit=3)
            logger.info("Returning knowledge search response")
            return {
                "type": "knowledge",
                "answer": knowledge_response.get("answer", ""),
                "sources": knowledge_response.get("sources", []),
                "related_properties": related_properties,
            }

        return {
            "type": "knowledge",
            "answer": "",
            "sources": [],
            "related_properties": [],
        }
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Bad request error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ExternalServiceError, PsycopgError, ConfigurationError) as exc:
        logger.exception("Service unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable") from exc
    except Exception as exc:
        logger.exception("Unexpected API error: %s", exc)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable") from exc


@app.post("/search", include_in_schema=False)
def legacy_search(req: Query):
    return chat(req)
