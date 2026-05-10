# Akasha Setup Guide

## Prerequisites

- macOS (Raycast integration is macOS-only)
- Python 3.12+ — `brew install python`
- Poetry — `brew install poetry`
- Node.js 20+ — `brew install node`
- [Obsidian](https://obsidian.md) installed with a vault
- [Raycast](https://raycast.com) installed

---

## 1. Install the API service

```bash
cd akasha-core
poetry install
```

On first run this downloads the fastembed embedding model (~33MB, ONNX).

## 2. Configure `.env`

```bash
cp akasha-core/.env.example akasha-core/.env
```

Edit `akasha-core/.env`:

```env
# Required
AKASHA_VAULT_PATH=/path/to/your/obsidian/vault

# Optional — defaults shown
AKASHA_CHROMA_PATH=~/.akasha/chroma
AKASHA_EMBEDDING_BACKEND=local
AKASHA_LOCAL_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
AKASHA_API_HOST=127.0.0.1
AKASHA_API_PORT=8765

# Required for /ask endpoint and ebook ingestion
AKASHA_ANTHROPIC_API_KEY=sk-ant-...
AKASHA_CLAUDE_MODEL=claude-sonnet-4-6
```

> **Vault location**: iCloud Drive works reliably. OneDrive with Files On-Demand can cause issues — pin the vault folder for offline access if using OneDrive.

## 3. Index your vault

```bash
cd akasha-core
poetry run akasha-index
```

Skips unchanged files on subsequent runs. To rebuild from scratch (e.g. after switching embedding models):

```bash
poetry run akasha-index --force
```

## 4. Start the API server

```bash
cd akasha-core
poetry run akasha-serve
```

The server starts on `http://localhost:8765`, watches your vault for changes, and re-indexes new or modified notes automatically.

```bash
curl http://localhost:8765/health
# {"status":"ok","vault":"...","notes":279}
```

## 5. Load the Raycast extension

```bash
cd extensions/raycast-akasha
npm install
npm run dev   # keep this running while developing
```

In Raycast:
1. Open **Settings** → **Extensions**
2. Click **`+`** → **Add Local Extension**
3. Select the `extensions/raycast-akasha` folder

Three commands will appear: **Search Akasha**, **Ask Akasha**, **Ingest Book**.

### Set extension preferences

In Raycast → Settings → Extensions → Akasha:

| Preference | Value |
|---|---|
| API URL | `http://localhost:8765` (default) |
| Obsidian Vault Name | Your vault name (e.g. `akasha`) |
| Akasha Core Directory | Absolute path to `akasha-core/` — enables auto-start |

With **Akasha Core Directory** set, the extension auto-starts `akasha-serve` when you first search, so you don't need to keep a terminal open.

### Set an alias for fast access

In Raycast → Settings → Extensions → Akasha → **Search Akasha** → set **Alias** to something short like `ak`. Then `ak` + Enter in Raycast opens the search immediately.

---

## Daily workflow

**Search**: Open Raycast → `ak` → type your query. Results appear live with score-coloured icons and query-relevant snippets. Press Enter to open in Obsidian.

**Ask a question**: Open Raycast → "Ask Akasha" → type your question → Enter. Claude synthesizes an answer from your notes with citations. Source notes are listed in the sidebar and can be opened directly.

**Ingest a book**: Open Raycast → "Ingest Book" → pick an EPUB or PDF → ⌘↵. A progress view shows each chapter being processed. When done, press Enter to open the book note in Obsidian.

---

## Ebook ingestion

Requires `AKASHA_ANTHROPIC_API_KEY`. Supported formats: `.epub`, `.pdf`.

From Raycast: "Ingest Book" command (recommended — live progress, zero terminal).

From terminal:
```bash
cd akasha-core
poetry run akasha-ingest /path/to/book.epub
```

Notes are written to `Books/{Book Title}/` in your vault and immediately indexed. Typical cost: $0.05–0.15 per book at Claude Sonnet rates.

---

## API reference

| Endpoint | Method | Body | Description |
|---|---|---|---|
| `/health` | GET | — | Server status + note count |
| `/stats` | GET | — | Vault path, model, total notes |
| `/search` | POST | `{query, limit?, threshold?}` | Semantic search |
| `/ask` | POST | `{question, limit?}` | RAG Q&A via Claude |
| `/ingest` | POST | `{path}` | Start background book ingestion |
| `/ingest/{job_id}` | GET | — | Poll job status and progress |

### Search

```bash
curl -X POST http://localhost:8765/search \
  -H "Content-Type: application/json" \
  -d '{"query": "managing stakeholders", "limit": 5}'
```

```json
{
  "results": [
    {
      "title": "12. Working with your stakeholders",
      "path": "Books/The Art of AI Product Development/12 - Working with your stakeholders.md",
      "snippet": "Chapter 12 focuses on stakeholder communication across three concentric rings...",
      "score": 0.73,
      "tags": ["stakeholders", "communication"],
      "modified": "2026-05-10T12:00:00"
    }
  ],
  "query_time_ms": 45.2,
  "total_notes": 279
}
```

`threshold`: minimum cosine similarity (0–1). Default `0.0`. Set to `0.5` to filter weak matches.

### Ask

```bash
curl -X POST http://localhost:8765/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How should I handle a difficult conversation with my manager?"}'
```

```json
{
  "answer": "## Handling a Difficult Conversation...\n\n...",
  "sources": [...],
  "query_time_ms": 18500.0
}
```

---

## Switching to OpenAI embeddings

```env
AKASHA_EMBEDDING_BACKEND=openai
AKASHA_OPENAI_API_KEY=sk-...
AKASHA_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Then force re-index (dimension change from 384 → 1536 requires full rebuild):

```bash
poetry run akasha-index --force
```

---

## Development setup

```bash
# Install pre-commit hooks (one-time)
brew install pre-commit
pre-commit install

# Run tests
cd akasha-core && poetry run pytest

# Lint
poetry run ruff check .

# Extension dev mode (hot-reload on save)
cd extensions/raycast-akasha && npm run dev
```

---

## Troubleshooting

**Server won't start — port already in use**
```bash
kill $(lsof -ti:8765)
```

**Search returns no results**
- Run `poetry run akasha-index` and confirm it completes without errors
- Check `AKASHA_VAULT_PATH` is correct
- `curl http://localhost:8765/stats` — confirm `total_notes > 0`

**Ask returns 503**
- `AKASHA_ANTHROPIC_API_KEY` is not set in `.env`

**Ingest fails mid-book**
- Verify `AKASHA_ANTHROPIC_API_KEY` is valid
- Some chapters with unusual formatting may fail; already-written notes are not overwritten — re-running picks up where it left off structurally (though Claude will re-process any remaining chapters)

**Raycast extension doesn't appear**
- Run `npm run dev` in `extensions/raycast-akasha` to trigger a build
- Reload extensions in Raycast if needed
