import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException

from .config import settings
from .models import NoteResult, SearchRequest, SearchResponse, StatsResponse
from . import embeddings, store, watcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    observer = watcher.start_watcher()
    yield
    observer.stop()
    observer.join()


app = FastAPI(title="Akasha", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "vault": str(settings.vault_path), "notes": store.count()}


@app.get("/stats", response_model=StatsResponse)
def stats():
    return StatsResponse(
        total_notes=store.count(),
        vault_path=str(settings.vault_path),
        chroma_path=str(settings.chroma_path),
        embedding_model=settings.embedding_model,
    )


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    t0 = time.perf_counter()
    query_embedding = embeddings.embed(req.query)
    raw = store.search(query_embedding, limit=req.limit, threshold=req.threshold)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    results = [
        NoteResult(
            title=r["metadata"].get("title", ""),
            path=r["metadata"].get("path", ""),
            snippet=r["snippet"],
            score=round(r["score"], 4),
            tags=[t for t in r["metadata"].get("tags", "").split(",") if t],
            modified=r["metadata"].get("modified"),
        )
        for r in raw
    ]

    return SearchResponse(
        results=results,
        query_time_ms=round(elapsed_ms, 1),
        total_notes=store.count(),
    )


def run():
    uvicorn.run("akasha.main:app", host=settings.api_host, port=settings.api_port)
