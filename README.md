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

### Current Phase: Foundation & Validation

- ✅ Project initialized
- ⬜ Obsidian vault setup with Smart Connections
- ⬜ Raycast integration configured
- ⬜ 2-4 week validation period
- ⬜ Document retrieval patterns and pain points

## Architecture

### Phase 1: Foundation (Current)

```bash
Obsidian (markdown notes)
    ↓
Smart Connections Plugin (semantic search within Obsidian)
    ↓
Raycast Extension (quick access from anywhere)
```

### Phase 2: Custom Retrieval Layer (Future)

```bash
Obsidian Vault (~/vault/)
    ↓
Akasha Core (FastAPI)
  - Vector embeddings
  - Semantic search
  - Context-aware retrieval
    ↓
Multiple Interfaces:
  - Raycast extension (macOS-wide access)
  - VS Code extension (coding context)
  - CLI tool (terminal workflow)
  - Web UI (review & curation)
```

## Repository Structure

```bash
akasha/
├── vault/                    # Obsidian notes (not in git by default)
├── docs/                     # Project documentation
│   ├── architecture.md       # Technical design decisions
│   ├── roadmap.md           # Development phases
│   └── setup.md             # Setup instructions
├── akasha-core/             # FastAPI service (Phase 2)
├── scripts/                 # Utility scripts
│   └── raycast/            # Raycast integration scripts
└── README.md               # This file
```

## Quick Start

### Prerequisites

- macOS (for Raycast integration)
- Obsidian installed
- Raycast installed

### Setup

1. **Configure Obsidian**

   ```bash
   # Create or link your vault
   ln -s ~/Documents/ObsidianVault ./vault
   ```

2. **Install Obsidian Plugins**

   - Smart Connections (for semantic search)
   - Any other preferred plugins

3. **Configure Raycast**
   - Install Obsidian extension from Raycast Store
   - Point to your vault location

See [docs/setup.md](docs/setup.md) for detailed instructions.

## Philosophy

### Start Simple, Customize When Justified

- Use existing tools (Obsidian, Raycast) for foundation
- Build custom components only when they solve validated problems
- Maintain data portability (markdown, JSON)
- Local-first, with cloud sync as option

### Hybrid Approach

- Managed tools for storage and editing (Obsidian)
- Custom AI layer for intelligent retrieval
- Thin clients for universal access

## Technology Stack

### Current (Phase 1)

- **Storage**: Obsidian (markdown files)
- **Semantic Search**: Smart Connections plugin
- **Quick Access**: Raycast + Obsidian extension

### Planned (Phase 2)

- **API**: FastAPI + Python 3.11+
- **Vector Store**: TBD (Pinecone, pgvector, or ChromaDB)
- **Embeddings**: OpenAI or sentence-transformers
- **File Watching**: watchdog
- **Clients**: Raycast extension (TypeScript), CLI (Python)

## Inspiration

The name "Akasha" comes from the Sanskrit concept of a cosmic record of all knowledge and events. This project aims to create your personal Akashic Records—a queryable repository of everything you've learned and thought about.

## License

MIT (or your preference)

## Author

Jim Correll - Lead Developer
