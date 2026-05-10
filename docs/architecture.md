# Akasha Architecture

Technical design, decisions made, and how the system fits together.

---

## Design Principles

1. **Local-first** — all data and computation stays on your machine; no cloud dependency at runtime
2. **Data portability** — plain markdown files, standard formats, no lock-in
3. **Universal access** — query from any context (Raycast, future: VS Code, terminal)
4. **Semantic over keyword** — embeddings surface conceptually relevant notes, not just term matches
5. **Zero friction** — adding knowledge and querying it should require no context switching

---

## System Overview

```
┌───────────────────────────────────────────────────────────┐
│                  Obsidian Vault (Markdown)                 │
│                                                           │
│  Manual notes             Books/                          │
│  Daily notes              ├── Think Like a CTO/           │
│  Meeting notes            │   ├── Think Like a CTO.md     │
│  ...                      │   ├── 01 - Managing Up.md     │
│                           │   └── 02 - Building a Team.md │
│                           └── ...                          │
└──────────────────────────┬────────────────────────────────┘
                           │  watchdog (real-time file events)
                           ▼
┌───────────────────────────────────────────────────────────┐
│                Akasha Core  (FastAPI :8765)                │
│                                                           │
│  Indexer                                                  │
│  ├── Parses frontmatter (python-frontmatter)              │
│  ├── Extracts title, tags, body, content hash             │
│  ├── Build embed text:                                    │
│  │   ├── book-chapter: Summary + Takeaways + Frameworks   │
│  │   └── other: title + full body                        │
│  └── Upserts to ChromaDB (skip if hash unchanged)         │
│                                                           │
│  Embeddings                                               │
│  ├── fastembed BAAI/bge-small-en-v1.5 (384-dim, local)   │
│  └── OpenAI text-embedding-3-small (optional, 1536-dim)  │
│                                                           │
│  ChromaDB  (~/.akasha/chroma)                             │
│  ├── Cosine similarity collection "notes"                 │
│  └── Stores: embedding + metadata + full cleaned body     │
│                                                           │
│  API Endpoints                                            │
│  ├── POST /search  — embed query → similarity search      │
│  │                   → extract query-relevant passage     │
│  ├── POST /ask     — retrieve top notes → Claude RAG      │
│  ├── POST /ingest  — start background book job            │
│  ├── GET  /ingest/{id} — poll job status + progress      │
│  ├── GET  /health                                         │
│  └── GET  /stats                                          │
└──────────────────────────┬────────────────────────────────┘
                           │  HTTP (localhost only)
                           ▼
┌───────────────────────────────────────────────────────────┐
│           Raycast Extension  (TypeScript)                  │
│                                                           │
│  Search Akasha                                            │
│  ├── 300ms debounced live search                          │
│  ├── Split-pane: result list + detail (snippet, metadata) │
│  ├── Score colours: green ≥70%, yellow ≥50%, grey below  │
│  └── Actions: open Obsidian, copy URL, copy path          │
│                                                           │
│  Ask Akasha                                               │
│  ├── Free-text question entry                             │
│  ├── Detail view: full markdown answer + source sidebar   │
│  └── Actions: open sources, copy answer                   │
│                                                           │
│  Ingest Book                                              │
│  ├── File picker (EPUB / PDF)                             │
│  ├── Starts /ingest job, navigates to progress view       │
│  ├── Polls /ingest/{id} every 2s, shows chapter progress  │
│  └── On completion: "Open in Obsidian" action             │
└───────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### Embeddings: local fastembed over OpenAI

**Decision**: `BAAI/bge-small-en-v1.5` via fastembed (ONNX, 384 dimensions, runs locally).

**Rationale**: onnxruntime is already a transitive dependency of ChromaDB; no GPU needed; no API key; ~33MB model download once. Quality is sufficient for a personal vault at this scale. OpenAI (`text-embedding-3-small`, 1536-dim) is still supported via `AKASHA_EMBEDDING_BACKEND=openai` — switching requires `--force` re-index due to dimension mismatch.

### Vector store: ChromaDB

**Decision**: ChromaDB with cosine similarity, persisted to `~/.akasha/chroma`.

**Rationale**: zero-config local persistence; simple Python API; sufficient performance for hundreds to low thousands of notes. Migration to pgvector or Pinecone would be straightforward if scale demands it.

### Snippet storage: full cleaned body

**Decision**: Store the full cleaned note body in ChromaDB's `documents` field (not a short preview).

**Rationale**: Enables query-time passage extraction. At search time, `_relevant_snippet()` scores each line by query-term overlap and returns a window around the best match. This is significantly more useful than always showing the opening sentence.

### Embed text: section-aware for book chapters

**Decision**: For `type: book-chapter` notes, build embed text from `## Summary`, `## Key Takeaways`, and `## Frameworks` sections only — not the full body.

**Rationale**: The full note body includes headings, "My Notes" placeholders, and blockquote formatting that dilutes the embedding signal. The three knowledge sections are 100% signal.

### Ebook ingestion: Claude tool use

**Decision**: Use Claude's forced tool use (`tool_choice: {type: tool}`) rather than prompting for JSON.

**Rationale**: Raw JSON responses from Claude can contain unescaped quotes from verbatim book text, breaking parsing. Forced tool use returns `block.input` as an already-parsed dict, completely bypassing JSON parsing.

### Book chapter titles: TOC-first

**Decision**: Prefer `book.toc` (EPUB NAV/NCX) as the source of chapter titles, with first-write-wins to prevent sub-sections overwriting chapter titles.

**Rationale**: Heading text extracted from HTML is concatenated and loses word boundaries ("1What is platform engineering"). The EPUB TOC provides clean, pre-formatted titles.

### RAG context: XML-tagged note blocks

**Decision**: Pass retrieved notes to Claude in `<note index="N" title="..." path="...">` XML blocks.

**Rationale**: Claude reliably reads structured XML context and naturally attributes answers ("According to the chapter on Managing Up…"). Context is capped at 3,000 chars per note × 6 notes, keeping total context well within Claude's window.

### Background ingest jobs: daemon threads + in-memory store

**Decision**: `threading.Thread(daemon=True)` + simple in-memory dict, polled via `GET /ingest/{job_id}`.

**Rationale**: Ebook ingestion takes several minutes (one Claude call per chapter). The API must stay responsive. Daemon threads die with the process, which is fine — jobs are ephemeral by design. A task queue (Celery, RQ) would be over-engineered for a single-user local tool.

---

## Data Flow

### Indexing a note

```
File saved in Obsidian
  → watchdog fires FileModifiedEvent
  → _parse_note(): frontmatter + body extraction
  → compare content_hash → skip if unchanged
  → _build_embed_text(): section-aware for book chapters
  → embeddings.embed() → 384-dim vector
  → store.upsert(): vector + metadata + cleaned body → ChromaDB
```

### Searching

```
User types in Raycast (debounced 300ms)
  → POST /search {query, limit}
  → embeddings.embed(query) → query vector
  → ChromaDB cosine similarity → top N results
  → _relevant_snippet(body, query): score lines by term overlap
  → return NoteResult[]  with query-relevant snippets
```

### Asking a question

```
User submits question in Raycast
  → POST /ask {question, limit=6}
  → embed question → retrieve top 6 notes (threshold 0.3)
  → build XML context: <note> blocks with cleaned body
  → Claude: answer grounded in context, cite by note title
  → return AskResponse {answer, sources[]}
```

### Ingesting a book

```
User picks file in Raycast → POST /ingest {path}
  → validate: exists, .epub/.pdf, API key configured
  → jobs.create() → daemon thread starts
  → thread: extract_epub/pdf() → chapters[]
  → for each chapter:
       process_chapter() → Claude tool use → {summary, takeaways, ...}
       write_chapter_note() → .md in vault
       job.messages.append("✓ Chapter N: Title")
  → process_book_overview() → book index note
  → index_note() for all written .md files
  → job.status = "done", job.result = vault-relative path
Raycast polls GET /ingest/{id} every 2s → shows progress → opens Obsidian on done
```

---

## File Structure

```
akasha-core/akasha/
├── config.py      pydantic-settings, AKASHA_ env prefix
├── main.py        FastAPI app, all endpoints, _relevant_snippet, _run_ingest_job
├── indexer.py     _parse_note, _clean_body, _build_embed_text, index_vault
├── ingest.py      extract_epub/pdf, _call_claude_tool, write_chapter_note
├── ask.py         build_context (XML blocks), answer (Claude call)
├── jobs.py        Job dataclass, in-memory dict, thread-safe create/get
├── embeddings.py  embed() / embed_batch() dispatching to fastembed or OpenAI
├── store.py       ChromaDB upsert / delete / search / count
├── watcher.py     watchdog observer, re-indexes on file events
├── models.py      Pydantic models for all requests and responses
└── cli.py         akasha-index (typer), akasha-ingest (typer) CLI entry points
```

---

## CI / Quality

| Tool | Purpose |
|---|---|
| ruff | Lint + format (replaces flake8, black, isort) |
| pytest | 27 tests: API endpoints (mocked) + pure-function indexer logic |
| pre-commit | Runs ruff, format check, secret detection, TS build on every commit |
| GitHub Actions | Python (lint + test) + TypeScript (build) on every PR |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AKASHA_VAULT_PATH` | `~/vault/akasha` | Path to Obsidian vault |
| `AKASHA_CHROMA_PATH` | `~/.akasha/chroma` | ChromaDB persistence directory |
| `AKASHA_EMBEDDING_BACKEND` | `local` | `local` or `openai` |
| `AKASHA_LOCAL_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | fastembed model name |
| `AKASHA_OPENAI_API_KEY` | — | Required if backend is `openai` |
| `AKASHA_OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI model |
| `AKASHA_ANTHROPIC_API_KEY` | — | Required for `/ask` and ebook ingestion |
| `AKASHA_CLAUDE_MODEL` | `claude-sonnet-4-6` | Claude model for extraction + RAG |
| `AKASHA_API_HOST` | `127.0.0.1` | API bind address |
| `AKASHA_API_PORT` | `8765` | API port |
