# Akasha Project Structure

```
akasha/
├── README.md                    # Main project overview
├── QUICKSTART.md               # 15-minute setup guide
├── LICENSE                     # MIT License
├── CONTRIBUTING.md             # Contribution guidelines
├── .gitignore                  # Git ignore rules
│
├── docs/                       # Documentation
│   ├── setup.md               # Detailed setup instructions
│   ├── architecture.md        # Technical design & decisions
│   ├── roadmap.md            # Development phases & milestones
│   └── validation-notes.md   # Phase 1 findings tracker
│
├── scripts/                   # Utility scripts
│   └── raycast/              # Raycast integration
│       └── akasha-search.sh  # Simple search script (Phase 2)
│
├── akasha-core/              # FastAPI service (Phase 2)
│   └── README.md            # API documentation
│
└── vault/                    # Your Obsidian notes (not in git)
    └── (your notes here)
```

## File Purposes

### Root Level
- **README.md**: Project vision, current status, and quick links
- **QUICKSTART.md**: Get up and running in 15 minutes
- **LICENSE**: MIT License for open source
- **CONTRIBUTING.md**: Guidelines for contributors
- **.gitignore**: Keeps your personal notes private

### Documentation (`/docs`)
- **setup.md**: Comprehensive setup guide for each phase
- **architecture.md**: Technical decisions, design patterns, tech stack
- **roadmap.md**: Development timeline, milestones, decision points
- **validation-notes.md**: Track your Phase 1 findings

### Scripts (`/scripts`)
- **raycast/akasha-search.sh**: Template for future Raycast integration

### API (`/akasha-core`)
- Placeholder for Phase 2 FastAPI service
- Will contain: app/, tests/, requirements, config

### Vault (`/vault`)
- Your Obsidian notes (excluded from git by default)
- Can be symlink to existing vault
- Contains all your knowledge

## Next Steps

1. Read [QUICKSTART.md](../QUICKSTART.md) to get started
2. Follow [docs/setup.md](setup.md) for detailed instructions
3. Use [docs/validation-notes.md](validation-notes.md) to track findings
4. Review [docs/roadmap.md](roadmap.md) to see where we're headed

## Current Phase

**Phase 1: Foundation & Validation** ✨

The project is currently in the validation phase. No code needs to be written yet - just set up Obsidian and Raycast, use them for 2-4 weeks, and document what works and what doesn't.

Phase 2 (custom API) begins only after Phase 1 validates the need.
