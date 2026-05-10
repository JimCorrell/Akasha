# Akasha

> Query the ether of your knowledge

Personal knowledge management system with AI-powered semantic retrieval. Akasha surfaces relevant notes and insights exactly when you need them — from anywhere on your Mac.

## What it does

- **Search your vault** with natural language from Raycast — results ranked by semantic similarity, not keyword match
- **Ask questions** and get synthesized answers drawn from your notes, with source citations
- **Ingest ebooks** (EPUB or PDF) into structured, searchable vault notes — one note per chapter, all via Raycast with live progress
- **Auto-indexes** as you write — vault watcher picks up new and changed notes in real time

## Project Status

Everything below is built and in daily use.

| Component | Status |
|---|---|
| FastAPI semantic search service | ✅ |
| Local embeddings (fastembed, no API key) | ✅ |
| ChromaDB vector store | ✅ |
| Vault file watcher (auto-index on save) | ✅ |
| Ebook ingestion: EPUB + PDF → Claude → vault notes | ✅ |
| Raycast extension: Search, Ask, Ingest Book | ✅ |
| Query-relevant snippet extraction | ✅ |
| RAG `/ask` endpoint with Claude | ✅ |
| Background ingest job API | ✅ |
| Pre-commit hooks + GitHub Actions CI | ✅ |

## Architecture

```
Obsidian Vault (markdown files)
        │
        ├── Manual notes
        └── Books/ (EPUB/PDF → Claude API → structured notes)
        │
        ↓  watchdog file watcher
┌─────────────────────────────────────────┐
│     Akasha Core  (FastAPI :8765)        │
│                                         │
│  /search  — semantic search             │
│  /ask     — RAG Q&A via Claude          │
│  /ingest  — background book ingestion   │
│  /health  /stats                        │
│                                         │
│  fastembed (BAAI/bge-small-en-v1.5)     │
│  ChromaDB (~/.akasha/chroma)            │
└─────────────────────────────────────────┘
        │
        ↓  HTTP
┌─────────────────────────────────────────┐
│  Raycast Extension (TypeScript)         │
│                                         │
│  Search Akasha  — live semantic search  │
│  Ask Akasha     — Q&A with citations   │
│  Ingest Book    — file picker + progress│
└─────────────────────────────────────────┘
```

## Quick Start

See **[Setup Guide](docs/setup.md)** for full instructions. The short version:

```bash
# 1. Install and configure
cd akasha-core
poetry install
cp .env.example .env   # edit AKASHA_VAULT_PATH + AKASHA_ANTHROPIC_API_KEY

# 2. Index your vault
poetry run akasha-index

# 3. Start the server
poetry run akasha-serve

# 4. Load the Raycast extension
# Raycast → Settings → Extensions → + → Add Local Extension → extensions/raycast-akasha
```

## Repository Structure

```
akasha/
├── akasha-core/              # FastAPI service (Python)
│   ├── akasha/
│   │   ├── config.py         # Settings via pydantic-settings (AKASHA_ prefix)
│   │   ├── main.py           # FastAPI app + endpoints
│   │   ├── indexer.py        # Vault scanning, embedding, change detection
│   │   ├── ingest.py         # Ebook pipeline: extract → Claude → vault notes
│   │   ├── ask.py            # RAG: context building + Claude answer generation
│   │   ├── jobs.py           # In-memory background job tracker
│   │   ├── embeddings.py     # fastembed (local) or OpenAI backend
│   │   ├── store.py          # ChromaDB operations
│   │   ├── watcher.py        # watchdog vault file watcher
│   │   ├── models.py         # Pydantic request/response models
│   │   └── cli.py            # akasha-index, akasha-ingest CLI entry points
│   └── tests/
│       ├── test_api.py       # FastAPI endpoint tests (mocked deps)
│       └── test_indexer.py   # Pure-function indexer tests
├── extensions/raycast-akasha/ # Raycast extension (TypeScript)
│   └── src/
│       ├── search.tsx         # Live search with split-pane detail
│       ├── ask.tsx            # Question → synthesized answer
│       └── ingest.tsx         # File picker → live progress → Obsidian
├── scripts/raycast/           # Legacy script commands (superseded by extension)
├── docs/                      # Architecture, setup, roadmap
└── .github/workflows/ci.yml  # Python lint+test + TypeScript build
```

## Development

```bash
# Run tests
cd akasha-core && poetry run pytest

# Lint
poetry run ruff check .

# Pre-commit hooks (runs on every git commit)
brew install pre-commit && pre-commit install

# Raycast extension dev mode (hot-reload)
cd extensions/raycast-akasha && npm run dev
```

## Documentation

- [Setup Guide](docs/setup.md) — installation, configuration, first run
- [Architecture](docs/architecture.md) — technical decisions and design
- [Roadmap](docs/roadmap.md) — what's been built, what's next
