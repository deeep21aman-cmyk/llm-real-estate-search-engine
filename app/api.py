from dotenv import load_dotenv


load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
from RealtorDR.app.main_pipeline import run_property_search
from RealtorDR.app.intent_parser import detect_intent

app = FastAPI()


def search_transcripts(query):
    from KNOWLEDGE.app.search import search_transcripts as knowledge_search

    return knowledge_search(query)

class Query(BaseModel):
    query: str



@app.post("/chat")
def chat(req: Query):
    query = req.query

    intent = detect_intent(query)

    if intent == "PROPERTY_SEARCH":
        property_response = run_property_search(query)
        return {
            "type": "property",
            **property_response,
        }

    elif intent == "KNOWLEDGE_SEARCH":
        knowledge_response = search_transcripts(query)
        return {
            "type": "knowledge",
            "answer": knowledge_response.get("answer", ""),
            "sources": knowledge_response.get("sources", []),
        }

    return {
        "type": "knowledge",
        "answer": "",
        "sources": [],
    }


@app.post("/search", include_in_schema=False)
def legacy_search(req: Query):
    return chat(req)
