# Akasha Setup Guide

Complete setup instructions for getting Akasha up and running.

## Phase 1: Foundation Setup

This phase focuses on validating the semantic retrieval workflow using existing tools.

### 1. Obsidian Setup

#### Install Obsidian
Download from: https://obsidian.md

#### Create or Link Your Vault

**Option A: Create New Vault**
```bash
cd akasha
mkdir vault
```
Then in Obsidian: "Open folder as vault" → select `akasha/vault`

**Option B: Use Existing Vault**
```bash
cd akasha
ln -s ~/path/to/your/existing/vault ./vault
```

#### Install Required Plugins

1. Open Obsidian Settings → Community Plugins
2. Disable Safe Mode
3. Browse and install:
   - **Smart Connections** (required for semantic search)
   - **Templater** (optional, for note templates)
   - **Dataview** (optional, for note queries)

#### Configure Smart Connections

1. Settings → Smart Connections
2. Set OpenAI API key (or use local model)
3. Configure embedding model (default: text-embedding-ada-002)
4. Enable "Show Smart Connections" in sidebar

### 2. Raycast Setup

#### Install Raycast
Download from: https://raycast.com

#### Configure Hotkey
1. Raycast Preferences → General
2. Set Raycast Hotkey (recommend: `Option + Space`)
3. This keeps `Cmd + Space` for Spotlight if desired

#### Install Obsidian Extension

1. Open Raycast
2. Type "Store" → Enter
3. Search "Obsidian"
4. Install the Obsidian extension
5. Configure vault path in extension settings

#### Test Integration

1. Press Raycast hotkey
2. Type "Search Obsidian" or just start typing note names
3. Should see your notes appear

### 3. Optional: Readwise Integration

For automatic highlight capture from books, articles, podcasts.

1. Sign up at: https://readwise.io ($8/mo after trial)
2. Connect your reading sources (Kindle, Instapaper, etc.)
3. Enable Obsidian export in Readwise settings
4. Configure export location to your vault

### 4. Initial Note Structure

Consider organizing your vault:

```
vault/
├── inbox/              # Quick captures, unsorted
├── areas/              # Ongoing topics (work, health, hobbies)
├── projects/           # Active projects
├── resources/          # Reference material
└── archive/            # Completed or inactive
```

Or use whatever structure works for you—Akasha will handle retrieval regardless.

### 5. Validation Period

**Goal**: Use this setup for 2-4 weeks and track:

✅ When semantic search helps vs. keyword search
✅ When you still rely on memory instead of searching
✅ What contexts you want to query from (VS Code, browser, etc.)
✅ What automation would help (capture, linking, etc.)

**Document your findings** in `docs/validation-notes.md`

## Phase 2: Custom API Setup (Future)

This section will be populated when you're ready to build the custom retrieval layer.

### Prerequisites (TBD)
- Python 3.11+
- Poetry or pip
- PostgreSQL (if using pgvector)
- OpenAI API key or local LLM

### Installation (TBD)
Instructions will be added after Phase 1 validation.

## Troubleshooting

### Obsidian Smart Connections not working
- Check OpenAI API key is set correctly
- Verify you have credits in your OpenAI account
- Try regenerating embeddings: Command Palette → "Smart Connections: Regenerate Embeddings"

### Raycast can't find notes
- Verify vault path in Raycast Obsidian extension settings
- Rebuild Raycast index: Command Palette → "Rebuild Index"

### Notes not syncing
- If using multiple devices, consider Obsidian Sync ($8/mo) or iCloud/Dropbox
- Git is also an option for technical users

## Next Steps

After setup:
1. Start capturing notes regularly
2. Test semantic search with Smart Connections
3. Use Raycast for quick access
4. Document what works and what doesn't
5. After 2-4 weeks, review findings and decide on Phase 2

## Questions?

Create an issue in the repo or update the documentation as you learn!
