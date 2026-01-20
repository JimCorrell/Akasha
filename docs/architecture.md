# Akasha Architecture

Technical design decisions and architecture evolution.

## Design Principles

1. **Hybrid Approach**: Use existing tools for their strengths, build custom only when justified
2. **Data Portability**: Simple formats (markdown, JSON) that survive tool changes
3. **Local-First**: Your data lives on your machine, cloud sync is optional
4. **Universal Access**: Query from any work context (coding, writing, browsing)
5. **Semantic Intelligence**: AI-powered retrieval beats keyword search

## Phase 1: Foundation (Current)

**Goal**: Validate that semantic retrieval actually improves workflow.

### Architecture

```
┌─────────────────────────────────────────┐
│         Obsidian Vault (Markdown)       │
│  - Simple, portable storage             │
│  - Manual and automated capture         │
└──────────────┬──────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│    Smart Connections Plugin (Obsidian)   │
│  - Generates embeddings via OpenAI       │
│  - In-app semantic search                │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│      Raycast Obsidian Extension          │
│  - macOS-wide quick access               │
│  - Keyword search + file opening         │
└──────────────────────────────────────────┘
```

### Technology Stack

- **Storage**: Obsidian (markdown files)
- **Semantic Search**: Smart Connections (OpenAI embeddings)
- **Quick Access**: Raycast
- **Capture**: Manual entry + optional Readwise

### Limitations

- Semantic search only available within Obsidian
- No context-aware retrieval (doesn't know what you're working on)
- Switching to Obsidian breaks flow
- Can't query from VS Code, browser, terminal

### Success Criteria

Phase 1 is successful if:
- Semantic search surfaces useful notes >50% of the time
- You actively use search instead of relying on memory
- Clear pain points emerge that justify custom development

## Phase 2: Custom Retrieval Layer (Planned)

**Goal**: Build universal semantic retrieval that works from any context.

### Architecture

```
┌─────────────────────────────────────────┐
│         Obsidian Vault (Markdown)       │
│  - File system accessible               │
└──────────────┬──────────────────────────┘
               │
               ↓ (watches for changes)
┌──────────────────────────────────────────┐
│         Akasha Core (FastAPI)            │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Vault Watcher (watchdog)          │ │
│  │  - Detects file changes            │ │
│  │  - Triggers embedding generation   │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Embedding Service                 │ │
│  │  - OpenAI API or local models      │ │
│  │  - Generates vector embeddings     │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Vector Store                      │ │
│  │  - Pinecone / pgvector / ChromaDB  │ │
│  │  - Similarity search               │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Search API                        │ │
│  │  POST /search                      │ │
│  │  - Accepts query + context         │ │
│  │  - Returns ranked results          │ │
│  └────────────────────────────────────┘ │
└──────────────┬───────────────────────────┘
               │
               ↓ (HTTP requests)
┌──────────────────────────────────────────┐
│         Multiple Clients                 │
│                                          │
│  ┌────────────────┐  ┌────────────────┐ │
│  │ Raycast Ext.   │  │ VS Code Ext.   │ │
│  │ - Global hotkey│  │ - In-editor    │ │
│  └────────────────┘  └────────────────┘ │
│                                          │
│  ┌────────────────┐  ┌────────────────┐ │
│  │ CLI Tool       │  │ Web UI         │ │
│  │ - Terminal use │  │ - Review/curate│ │
│  └────────────────┘  └────────────────┘ │
└──────────────────────────────────────────┘
```

### Technology Stack (Proposed)

**Backend**
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Vector Store**: TBD after research
  - Pinecone (cloud, easy)
  - pgvector (self-hosted, PostgreSQL)
  - ChromaDB (simple, local-first)
- **Embeddings**: OpenAI text-embedding-3-small or sentence-transformers
- **File Watching**: watchdog
- **Task Queue**: Optional (for async embedding generation)

**Clients**
- **Raycast**: TypeScript + Raycast API
- **CLI**: Python click or typer
- **VS Code**: TypeScript + VS Code Extension API
- **Web UI**: React or vanilla JS (minimal)

### Data Flow

1. **Ingestion**
   - User creates/edits note in Obsidian
   - Vault watcher detects change
   - Akasha extracts text + metadata
   - Generates embedding
   - Stores in vector DB with reference to file path

2. **Retrieval**
   - User triggers search from any client
   - Client sends query + optional context to API
   - API generates query embedding
   - Vector DB returns similar notes
   - API ranks and returns results with snippets
   - Client displays results with actions (open, copy, etc.)

3. **Context Enhancement** (future)
   - Detect active application (VS Code, browser, etc.)
   - Extract current file/page context
   - Weight search results by relevance to current work

### API Design (Draft)

```python
# POST /search
{
  "query": "fastapi authentication patterns",
  "context": {
    "app": "vscode",
    "file": "/path/to/current/file.py",
    "recent_files": [...],
    "workspace": "project-name"
  },
  "limit": 5,
  "threshold": 0.7  # Minimum similarity score
}

# Response
{
  "results": [
    {
      "title": "FastAPI PKI Authentication",
      "path": "dev/fastapi-auth.md",
      "snippet": "Implementation notes on certificate-based...",
      "score": 0.92,
      "created": "2024-01-15T10:30:00Z",
      "modified": "2024-01-20T14:22:00Z",
      "tags": ["python", "auth", "fastapi"]
    }
  ],
  "query_embedding_time_ms": 45,
  "search_time_ms": 12,
  "total_notes": 347
}
```

### Database Schema (Vector Store)

```python
# Conceptual schema (actual implementation varies by store)
class NoteEmbedding:
    id: str                    # UUID
    file_path: str            # Relative to vault root
    title: str                # Extracted from frontmatter or filename
    content_hash: str         # For change detection
    embedding: List[float]    # 1536-dim for OpenAI, varies for others
    metadata: dict            # Tags, dates, custom fields
    chunk_index: int          # If splitting long notes
    created_at: datetime
    updated_at: datetime
```

### Scaling Considerations

**Current Scale** (estimated):
- ~500-1000 notes
- ~10 notes added per week
- Single user, local access

**Design Decisions**:
- Start simple: ChromaDB for local development
- Easy migration path to Pinecone or pgvector if needed
- Batch embedding generation (process 10 notes at a time)
- Cache embeddings (don't regenerate unless content changed)

### Security & Privacy

- **Local-First**: All data stays on your machine by default
- **API Access**: Localhost only initially, no external exposure
- **API Keys**: Stored in environment variables, never in code
- **Vault Access**: Read-only for Akasha Core
- **No Analytics**: Zero telemetry, your data is yours

## Phase 3: Advanced Features (Future)

Potential additions based on Phase 2 learnings:

- **Automatic Linking**: Suggest connections between notes
- **Topic Clustering**: Visualize knowledge domains
- **Temporal Analysis**: Track how ideas evolve over time
- **Multi-Modal**: Support for images, PDFs, code snippets
- **Collaborative**: Share specific notes or collections
- **Mobile**: iOS/Android companion apps

## Decision Log

### Vector Store Selection (TBD)

**Options Considered**:

1. **Pinecone**
   - ✅ Managed, no maintenance
   - ✅ Fast, reliable
   - ❌ Cloud dependency
   - ❌ Cost ($70+/mo at scale)

2. **pgvector**
   - ✅ Self-hosted, full control
   - ✅ Leverages existing PostgreSQL knowledge
   - ❌ Setup complexity
   - ❌ Performance tuning needed

3. **ChromaDB**
   - ✅ Simple, local-first
   - ✅ Good for development
   - ❌ Less battle-tested at scale
   - ✅ Easy migration path to others

**Decision**: Start with ChromaDB for Phase 2 prototype. Reevaluate if performance becomes an issue.

### Embedding Model (TBD)

**Options**:

1. **OpenAI text-embedding-3-small**
   - ✅ High quality, proven
   - ✅ 1536 dimensions
   - ❌ API cost (~$0.02/1M tokens)
   - ❌ Cloud dependency

2. **sentence-transformers (local)**
   - ✅ Free, runs locally
   - ✅ Privacy (no external calls)
   - ❌ Requires GPU for speed
   - ❌ Quality varies by model

**Decision**: Start with OpenAI for quality, add local option later for privacy-conscious users.

## Questions to Answer in Phase 1

- [ ] How often do you actually use semantic search vs. keyword?
- [ ] What contexts trigger the need to search notes?
- [ ] How important is speed? (sub-second vs. a few seconds)
- [ ] Would automated capture (Readwise, etc.) add value?
- [ ] What metadata would improve search? (tags, dates, projects)
- [ ] Is context-awareness worth the complexity?

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Raycast Extension API](https://developers.raycast.com/)
