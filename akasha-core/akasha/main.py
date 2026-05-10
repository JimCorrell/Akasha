import re
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


def _relevant_snippet(body: str, query: str, window: int = 400) -> str:
    """Return the passage in body most relevant to the query terms."""
    if not body:
        return ""

    # Meaningful query terms (skip short stop words)
    terms = [t.lower() for t in re.split(r"\W+", query) if len(t) > 2]

    # Candidate lines: non-empty, not headings, not list-only markers
    lines = [
        l.strip()
        for l in body.splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    if not lines:
        return body[:window]

    if not terms:
        return " ".join(lines)[:window]

    # Score each line by how many query terms it contains
    scores = []
    for line in lines:
        lower = line.lower()
        scores.append(sum(1 for t in terms if t in lower))

    best_idx = max(range(len(scores)), key=lambda i: scores[i])

    # Grab a window of lines centred on the best match
    start = max(0, best_idx - 1)
    end = min(len(lines), best_idx + 4)
    snippet = " ".join(lines[start:end])

    # If best line had zero term matches, fall back to opening passage
    if scores[best_idx] == 0:
        snippet = " ".join(lines[:5])

    return snippet[:window]


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
            snippet=_relevant_snippet(r["snippet"], req.query),
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
