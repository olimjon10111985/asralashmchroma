import chromadb
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Oddiy in-memory Chroma client. Railway'da bu servis alohida app sifatida ishlaydi.
client = chromadb.Client()
collection = client.get_or_create_collection(name="diary_entries")


class Entry(BaseModel):
    id: str  # masalan, "user_1_2025-11-21_1"
    user_id: int
    text: str
    created_at: Optional[str] = None


class UpsertRequest(BaseModel):
    entries: List[Entry]


class QueryRequest(BaseModel):
    user_id: int
    question: str
    top_k: int = 5


@app.post("/upsert_entries")
async def upsert_entries(payload: UpsertRequest):
    if not payload.entries:
        return {"status": "ok", "count": 0}

    ids = [e.id for e in payload.entries]
    documents = [e.text for e in payload.entries]
    metadatas = [
        {"user_id": str(e.user_id), "created_at": e.created_at or ""}
        for e in payload.entries
    ]

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return {"status": "ok", "count": len(ids)}


@app.post("/query")
async def query_entries(payload: QueryRequest):
    result = collection.query(
        query_texts=[payload.question],
        n_results=payload.top_k,
        where={"user_id": str(payload.user_id)},
    )
    docs = result.get("documents") or [[]]
    metas = result.get("metadatas") or [[]]

    hits = [
        {"text": d, "metadata": m}
        for d, m in zip(docs[0], metas[0])
    ]
    return {"hits": hits}
