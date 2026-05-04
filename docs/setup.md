# Akasha Setup Guide

## Prerequisites

- macOS (Raycast integration is macOS-only)
- Python 3.12+ — `brew install python`
- Poetry — `brew install poetry`
- [Obsidian](https://obsidian.md) installed
- [Raycast](https://raycast.com) installed

---

## 1. Install the API service

```bash
cd akasha-core
poetry install
```

## 2. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Required
AKASHA_VAULT_PATH=/path/to/your/obsidian/vault

# Optional — defaults work for most setups
AKASHA_CHROMA_PATH=~/.akasha/chroma
AKASHA_EMBEDDING_BACKEND=local
AKASHA_LOCAL_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
AKASHA_API_HOST=127.0.0.1
AKASHA_API_PORT=8765

# Required only for ebook ingestion
AKASHA_ANTHROPIC_API_KEY=sk-ant-...
AKASHA_CLAUDE_MODEL=claude-sonnet-4-6
```

**Vault location note**: iCloud Drive works reliably with Obsidian on macOS. OneDrive can cause sync issues with the Files On-Demand feature — if using OneDrive, pin the vault folder for offline access.

## 3. Index your vault

```bash
cd akasha-core
poetry run akasha-index
```

On first run this downloads the embedding model (~33MB). Subsequent runs skip unchanged files.

To force a full re-index (e.g. after changing embedding model):

```bash
poetry run akasha-index --force
```

## 4. Start the API server

```bash
poetry run akasha-serve
```

The server runs on `http://localhost:8765` and watches your vault for changes, re-indexing new or modified notes automatically.

Verify it's running:

```bash
curl http://localhost:8765/health
```

## 5. Set up Raycast

1. Open Raycast → **Settings** → **Extensions** → **Script Commands**
2. Click **Add Directories** and add:
   ```
   /path/to/akasha/scripts/raycast
   ```
3. Two commands will appear: **Akasha Search** and **Akasha Open Note**

**Akasha Search** auto-starts the API server if it's not running, so you don't need to keep a terminal open.

---

## Ingesting Ebooks

Akasha can process EPUB and PDF ebooks into structured vault notes (one note per chapter, plus a book index note).

**Requires** `AKASHA_ANTHROPIC_API_KEY` in `.env`.

```bash
cd akasha-core
poetry run akasha-ingest /path/to/book.epub
poetry run akasha-ingest /path/to/book.pdf
```

Notes are written to `Books/{Book Title}/` in your vault and indexed automatically.

Typical cost: ~$0.05–0.15 per book at Claude Sonnet rates.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Server status + note count |
| `/stats` | GET | Vault path, model, total notes |
| `/search` | POST | Semantic search |

### Search request

```json
{
  "query": "your question",
  "limit": 5,
  "threshold": 0.0
}
```

`threshold` is minimum cosine similarity (0–1). Set to `0.5` to filter weak matches.

### Search response

```json
{
  "results": [
    {
      "title": "Note Title",
      "path": "relative/path/to/note.md",
      "snippet": "First line of note content...",
      "score": 0.812,
      "tags": ["tag1", "tag2"],
      "modified": "2026-05-04T15:00:00"
    }
  ],
  "query_time_ms": 45.2,
  "total_notes": 142
}
```

---

## Switching to OpenAI Embeddings

If you prefer OpenAI embeddings over the local model:

```env
AKASHA_EMBEDDING_BACKEND=openai
AKASHA_OPENAI_API_KEY=sk-...
AKASHA_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**Important**: switching embedding backends requires a full re-index because vector dimensions differ (384 local vs 1536 OpenAI):

```bash
poetry run akasha-index --force
```

---

## Troubleshooting

**Server won't start — address already in use**
```bash
kill $(lsof -ti:8765)
```

**Search returns no results**
- Check `akasha-index` has been run and completed without errors
- Verify `AKASHA_VAULT_PATH` points to the right directory
- Run `curl http://localhost:8765/stats` to confirm note count > 0

**Ebook ingestion fails mid-book**
- Check `AKASHA_ANTHROPIC_API_KEY` is set correctly
- The book may have a chapter with unusual formatting — re-run; already-written notes are not overwritten
