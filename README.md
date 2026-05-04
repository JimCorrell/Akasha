# Akasha

> Query the ether of your knowledge

Personal knowledge management system with AI-powered semantic retrieval. Akasha surfaces relevant notes and insights exactly when you need them, across all your work environments.

## Vision

A "second brain" that:

- Automatically semantically links stored knowledge over time
- Surfaces ideas contextually as you work on projects
- Works seamlessly whether you're coding, writing, or researching
- Respects your data ownership (local-first, simple formats)

## Project Status

### Current Phase: Custom Retrieval Layer (Phase 2 — In Progress)

- ✅ Project initialized
- ✅ Phase 1 skipped — vault-only workflow validated as insufficient
- ✅ FastAPI semantic search service (`akasha-core/`)
- ✅ Local embeddings via fastembed (no API key required)
- ✅ ChromaDB vector store
- ✅ Vault file watcher (auto-indexes on save)
- ✅ Raycast integration (search from anywhere)
- ✅ Ebook ingestion pipeline (EPUB + PDF → structured vault notes)
- ⬜ Retrieval quality tuning (Phase 2.2)
- ⬜ Context-aware retrieval (Phase 2.4)
- ⬜ Full TypeScript Raycast extension (Phase 3)

## Architecture

```
Obsidian Vault (markdown files)
        │
        ├── Manual notes
        └── Ingested books (EPUB/PDF → Claude API → structured notes)
        │
        ↓ (watchdog file watcher)
Akasha Core (FastAPI — localhost:8765)
  ├── Embedding Service (fastembed, local — no API key)
  ├── Vector Store (ChromaDB at ~/.akasha/chroma)
  └── Search API (POST /search)
        │
        ↓ (HTTP)
Raycast Script Commands
  ├── Akasha Search  — semantic search from anywhere
  └── Akasha Open    — open note directly in Obsidian
```

## Repository Structure

```
akasha/
├── akasha-core/              # FastAPI service
│   ├── akasha/
│   │   ├── config.py         # Settings (env-driven)
│   │   ├── main.py           # FastAPI app + vault watcher
│   │   ├── indexer.py        # Vault scanning + embedding
│   │   ├── ingest.py         # Ebook ingestion pipeline
│   │   ├── store.py          # ChromaDB wrapper
│   │   ├── embeddings.py     # fastembed / OpenAI backends
│   │   ├── watcher.py        # watchdog file watcher
│   │   └── cli.py            # akasha-index / akasha-ingest commands
│   ├── pyproject.toml
│   └── .env.example
├── scripts/
│   └── raycast/              # Raycast Script Commands
│       ├── akasha-search.py  # Semantic search
│       └── akasha-open.py    # Open note in Obsidian
├── docs/                     # Documentation
│   ├── architecture.md
│   ├── roadmap.md
│   ├── setup.md
│   └── validation-notes.md
├── vault/                    # Obsidian notes (excluded from git)
└── books_to_ingest/          # Drop ebooks here (excluded from git)
```

## Quick Start

### Prerequisites

- macOS
- Python 3.12+ (via Homebrew: `brew install python`)
- Poetry (`brew install poetry`)
- Obsidian
- Raycast

### Install

```bash
cd akasha-core
poetry install
cp .env.example .env
# Edit .env — set AKASHA_VAULT_PATH at minimum
```

### Index your vault

```bash
poetry run akasha-index
```

### Start the API server

```bash
poetry run akasha-serve
# Runs on http://localhost:8765
# Watches vault for changes and re-indexes automatically
```

### Ingest an ebook

```bash
# Requires AKASHA_ANTHROPIC_API_KEY in .env
poetry run akasha-ingest /path/to/book.epub
poetry run akasha-ingest /path/to/book.pdf
```

### Search

```bash
# Via curl
curl -s -X POST http://localhost:8765/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here", "limit": 5}'

# Via Raycast (after setup — see docs/setup.md)
# ⌘ Space → "Akasha Search" → type your query
```

## Configuration

All settings are prefixed with `AKASHA_` in `.env`:

| Variable | Default | Description |
|---|---|---|
| `VAULT_PATH` | `~/vault/akasha` | Path to your Obsidian vault |
| `CHROMA_PATH` | `~/.akasha/chroma` | ChromaDB data directory |
| `EMBEDDING_BACKEND` | `local` | `local` or `openai` |
| `LOCAL_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | fastembed model |
| `API_HOST` | `127.0.0.1` | Server host |
| `API_PORT` | `8765` | Server port |
| `ANTHROPIC_API_KEY` | _(empty)_ | Required for ebook ingestion |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Model used for ingestion |

## Technology Stack

- **API**: FastAPI + uvicorn (Python 3.14)
- **Vector Store**: ChromaDB (local, persistent)
- **Embeddings**: fastembed `BAAI/bge-small-en-v1.5` (local, no API key)
- **File Watching**: watchdog
- **Ebook Ingestion**: ebooklib (EPUB), PyMuPDF (PDF), Claude API (summarization)
- **Dependency Management**: Poetry
- **Clients**: Raycast Script Commands (Python)

## Philosophy

### Local-First

All data lives on your machine. The vector store, embeddings, and vault are local by default. No telemetry, no cloud lock-in.

### Build Only What's Justified

Phase 1 (Obsidian + Smart Connections only) was validated as insufficient — the workflow didn't fit daily habits. Phase 2 builds the minimum custom layer needed: a search API and lightweight clients.

### Data Portability

Notes are plain markdown with YAML frontmatter. The vector store is a cache — if lost, `akasha-index --force` rebuilds it from the vault in minutes.

## Inspiration

The name "Akasha" comes from the Sanskrit concept of a cosmic record of all knowledge and events. This project aims to create your personal Akashic Records — a queryable repository of everything you've learned and thought about.

## License

MIT

## Author

Jim Correll
