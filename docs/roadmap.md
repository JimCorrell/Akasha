# Akasha Roadmap

---

## What's built

### Core API (`akasha-core/`)

| Feature | Notes |
|---|---|
| FastAPI semantic search service | Port 8765, localhost-only |
| Local embeddings | fastembed `BAAI/bge-small-en-v1.5`, 384-dim, ONNX, no GPU |
| OpenAI embeddings | Optional via `AKASHA_EMBEDDING_BACKEND=openai` |
| ChromaDB vector store | Cosine similarity, persisted to `~/.akasha/chroma` |
| Vault file watcher | watchdog, re-indexes on save in real time |
| Change detection | Content hash comparison — skips unchanged notes |
| `POST /search` | Embed query → similarity search → query-relevant snippets |
| `POST /ask` | RAG: retrieve notes → Claude → grounded answer with citations |
| `POST /ingest` | Start background book ingestion job, returns job ID |
| `GET /ingest/{id}` | Poll job status, messages, result path |
| `GET /health` / `/stats` | Server status and vault stats |

### Ebook ingestion

| Feature | Notes |
|---|---|
| EPUB extraction | ebooklib + BeautifulSoup, TOC-driven chapter titles |
| PDF extraction | PyMuPDF, TOC-driven or page-chunked fallback |
| Front matter filtering | Skips copyright, dedication, preface, index, Part sections |
| Chapter title cleaning | Strips "Chapter N:", "appendix", "N. ", "N - ", "N title" prefixes |
| Claude extraction | Forced tool use → summary, key_takeaways, frameworks, quotes, tags |
| Vault output | `Books/{Title}/` — one index note + one note per chapter |
| Auto-index after ingest | New notes immediately searchable |

### Search quality

| Feature | Notes |
|---|---|
| Query-relevant snippets | Scores each line by query-term overlap, returns best passage window |
| Section-aware embeddings | Book chapters embedded from Summary + Takeaways + Frameworks only |
| Full body storage | ChromaDB stores cleaned body for runtime passage extraction |

### Raycast extension (`extensions/raycast-akasha/`)

| Command | UX |
|---|---|
| Search Akasha | 300ms debounced live search, split-pane detail (snippet + metadata sidebar), score-coloured icons |
| Ask Akasha | Question entry → Detail view with markdown answer, source sidebar with Obsidian links |
| Ingest Book | File picker (EPUB/PDF) → live chapter-by-chapter progress → "Open in Obsidian" on completion |
| Auto-start | Server starts automatically if `akashaCoreDir` preference is set |

### CI / Quality

| Tool | What it gates |
|---|---|
| pre-commit: ruff | Lint + import sort on every commit (auto-fixed) |
| pre-commit: ruff-format | Formatting consistency |
| pre-commit: detect-private-key | Prevents accidental secret commits |
| pre-commit: raycast-build | TypeScript type-check when `src/` files change |
| GitHub Actions: python | ruff lint + format check + pytest (27 tests) on every PR |
| GitHub Actions: typescript | `npm ci` + `ray build` on every PR |

---

## What's next

Rough priority order — nothing is scheduled.

### 1. Retrieval quality — chunk-level search

Right now each note is one document in ChromaDB. For long book chapters, the embedding represents the whole chapter, which can bury the specific section that's actually relevant.

**Option A — chunk on ingest**: split each chapter into ~500-token overlapping chunks, store each as a separate ChromaDB document, return the best chunk's passage. Requires re-index.

**Option B — re-rank at query time**: retrieve more candidates (e.g. top 20) and re-rank by BM25 keyword overlap before returning top N. No re-index needed.

Option B is a faster win; Option A is the right long-term architecture.

### 2. VS Code extension

Search and ask from inside your editor, with the current file as implicit context. Adds the one client that's missing from the daily coding workflow.

Scope:
- Command palette: "Search Akasha" / "Ask Akasha"
- Results panel in sidebar
- Current file path sent as optional context to `/ask`
- Open result in Obsidian action

### 3. Context-aware retrieval

Weight search results by what you're currently working on. The API already accepts any query — the enhancement is automatically enriching it with context from the active application.

- Active VS Code file path → include in search query
- Active browser tab title/URL → extract keywords
- Recent clipboard content → optional context signal

Requires a small macOS helper (Swift or Objective-C) to read active application context, or an Electron-based approach.

### 4. Spaced repetition / surfacing

Periodically resurface notes you haven't visited in a while, weighted by semantic relevance to current work. A daily Raycast notification: "3 notes from your vault might be relevant to what you're working on."

### 5. Auto-linking suggestions

After ingesting new content, suggest wikilinks between notes that are semantically close but not yet linked. Could run as a CLI command (`akasha-suggest-links`) rather than automatically.

### 6. Note capture from Raycast

A "Capture" Raycast command: quick-add a note directly to the vault without opening Obsidian. Saves to a configurable inbox folder and indexes immediately. Could include a "capture + ask Akasha to expand it" flow.

### 7. Web UI for browsing

Simple local web interface for browsing, searching, and reviewing vault content without opening Obsidian. Useful for reviewing ingested books or exploring by tag.

---

## Anti-goals

Things Akasha will not do:

- Replace Obsidian for editing — Akasha is retrieval, not authoring
- Require cloud infrastructure or an internet connection at runtime
- Collect telemetry or usage data
- Lock content into proprietary formats
- Become a team or collaboration tool

---

## Decision log

| Decision | Choice | Rationale |
|---|---|---|
| Embedding model | fastembed `BAAI/bge-small-en-v1.5` (local) | onnxruntime already a ChromaDB dependency; free; private; sufficient quality for personal vault |
| Vector store | ChromaDB | Zero-config, local-first; easy migration path if scale demands |
| Snippet storage | Full cleaned body in ChromaDB documents | Enables query-time passage extraction vs. static first-line preview |
| Embed text | Section-aware for book chapters | Summary+Takeaways+Frameworks is pure signal; full body dilutes embeddings |
| Claude output format | Forced tool use | Avoids JSON parsing failures from unescaped quotes in verbatim book text |
| Chapter titles | EPUB TOC first-write-wins | HTML heading extraction concatenates text without word boundaries |
| Background jobs | Daemon threads + in-memory dict | Ingestion takes minutes; simple polling is fine for single-user local tool |
| RAG context format | XML `<note>` blocks | Claude reliably reads structured context and attributes naturally |

---

*Last updated: 2026-05-10*
