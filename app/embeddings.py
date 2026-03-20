from RealtorDR.app.config import EMBEDDING_MODEL
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
    response=client.embeddings.create(model=EMBEDDING_MODEL,input=text)
    
    return [item.embedding for item in response.data]

def get_embedding(text):
    response=client.embeddings.create(model=EMBEDDING_MODEL,input=[text])
    return response.data[0].embedding
