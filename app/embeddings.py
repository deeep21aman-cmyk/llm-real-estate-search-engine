from config import EMBEDDING_MODEL_NAME
from openai import OpenAI
import os

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError ("set API key")
    
client=OpenAI(api_key=OPENAI_API_KEY)

def embed_chunks(chunks:list[dict])-> list[list[float]]:
    
    if not chunks:
        return []
    text=[chunk["chunk_text"] for chunk in chunks]
    response=client.embeddings.create(model=EMBEDDING_MODEL_NAME,input=text)
    
    return [item.embedding for item in response.data]

def embed_query(query):
    embedded_query=client.embeddings.create(model=EMBEDDING_MODEL_NAME,input=[query])
    return embedded_query.data[0].embedding