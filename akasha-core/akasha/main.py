import re
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException

from .config import settings
from .models import (
    AskRequest, AskResponse,
    IngestJobResponse, IngestRequest,
    NoteResult, SearchRequest, SearchResponse, StatsResponse,
)
from . import ask as ask_module, embeddings, jobs, store, watcher


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


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="AKASHA_ANTHROPIC_API_KEY not configured")

    t0 = time.perf_counter()
    query_embedding = embeddings.embed(req.question)
    raw = store.search(query_embedding, limit=req.limit, threshold=0.3)

    if not raw:
        raise HTTPException(status_code=404, detail="No relevant notes found")

    answer_text = ask_module.answer(req.question, raw)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    sources = [
        NoteResult(
            title=r["metadata"].get("title", ""),
            path=r["metadata"].get("path", ""),
            snippet=_relevant_snippet(r["snippet"], req.question),
            score=round(r["score"], 4),
            tags=[t for t in r["metadata"].get("tags", "").split(",") if t],
            modified=r["metadata"].get("modified"),
        )
        for r in raw
    ]

    return AskResponse(
        answer=answer_text,
        sources=sources,
        query_time_ms=round(elapsed_ms, 1),
    )


def _run_ingest_job(job: jobs.Job, path: Path) -> None:
    """Background thread: ingest a book and update the job as it progresses."""
    try:
        from .ingest import ingest
        from .indexer import index_note

        def on_progress(msg: str) -> None:
            job.messages.append(msg)

        note_path = ingest(path, settings.vault_path, on_progress=on_progress)

        # Index the newly written notes immediately so they're searchable
        book_dir = note_path.parent
        for md in sorted(book_dir.glob("*.md")):
            index_note(md)

        # Return vault-relative path so Raycast can build the Obsidian URL
        job.result = str(note_path.relative_to(settings.vault_path))
        job.status = "done"
        job.messages.append(f"✅ Done — {note_path.name}")
    except Exception as e:
        job.error = str(e)
        job.status = "error"
        job.messages.append(f"❌ {e}")


@app.post("/ingest", response_model=IngestJobResponse)
def start_ingest(req: IngestRequest):
    path = Path(req.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {req.path}")
    if path.suffix.lower() not in (".epub", ".pdf"):
        raise HTTPException(status_code=400, detail="Only .epub and .pdf files are supported")
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="AKASHA_ANTHROPIC_API_KEY not configured")

    job = jobs.create()
    thread = threading.Thread(target=_run_ingest_job, args=(job, path), daemon=True)
    thread.start()

    return IngestJobResponse(job_id=job.id, status=job.status, messages=job.messages)


@app.get("/ingest/{job_id}", response_model=IngestJobResponse)
def ingest_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return IngestJobResponse(
        job_id=job.id,
        status=job.status,
        messages=job.messages,
        result=job.result,
        error=job.error,
    )


def run():
    uvicorn.run("akasha.main:app", host=settings.api_host, port=settings.api_port)
