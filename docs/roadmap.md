# Akasha Roadmap

Development phases and milestones for the Akasha project.

## Overview

Akasha follows a phased approach: validate the concept with existing tools, then build custom components only when justified by real usage patterns.

## Phase 1: Foundation & Validation

**Timeline**: 2-4 weeks  
**Status**: ✅ Complete (skipped — see validation-notes.md)

### Decision

Formal validation period skipped. Vault sat unused after setup — treated as the signal itself. The Obsidian-only workflow didn't fit daily habits; the friction of switching contexts to search was the core problem. Proceeded directly to Phase 2 on 2026-05-04.

---

## Phase 2: Custom Retrieval Layer

**Timeline**: 4-6 weeks  
**Status**: 🟡 In Progress  
**Prerequisites**: Phase 1 validated with clear pain points

### Goals
- Build FastAPI service for semantic search
- Implement basic Raycast integration script
- Support context-aware retrieval
- Maintain Obsidian as primary note interface

### Milestones

#### 2.1: Core API (Week 1-2) ✅
- [x] Project setup with Poetry
- [x] FastAPI basic structure
- [x] Vault file watcher implementation
- [x] Embedding generation pipeline (fastembed local model, OpenAI optional)
- [x] Vector store integration (ChromaDB)
- [x] Basic `/search` endpoint

#### 2.1b: Ebook Ingestion Pipeline ✅
- [x] EPUB extraction (ebooklib + BeautifulSoup)
- [x] PDF extraction (PyMuPDF, TOC-driven or page-chunked)
- [x] Claude API integration for chapter summarization (tool use, structured output)
- [x] Hierarchical vault notes: book index + one note per chapter
- [x] Chapter title cleaning (strips redundant "Chapter N:" prefixes)
- [x] `akasha-ingest` CLI command

#### 2.2: Retrieval Quality (Week 2-3)
- [ ] Snippet extraction improvements
- [ ] Result ranking and filtering
- [ ] Response time optimization (<500ms target)
- [ ] TOC-driven chapter extraction (accurate chapter numbers, front matter filtering)

#### 2.3: Raycast Integration (Week 3-4) ✅
- [x] Python Script Commands for Raycast (`scripts/raycast/`)
- [x] End-to-end search workflow tested
- [x] Formatted results with score bars and tags
- [x] File opening in Obsidian via `obsidian://` URLs
- [x] Auto-start server if not running

#### 2.4: Context Awareness (Week 4-5)
- [ ] Detect active application
- [ ] Extract current file context (VS Code, browser)
- [ ] Weight results by relevance to current work
- [ ] A/B test: context-aware vs. simple search

#### 2.5: Polish & Documentation (Week 5-6)
- [ ] Error handling and logging
- [ ] Configuration management
- [ ] API documentation
- [ ] User guide for setup
- [ ] Performance benchmarking

### Deliverables
- Working FastAPI service
- Raycast script for universal access
- Documentation for setup and usage
- Performance metrics and benchmarks

### Technology Decisions
- **Vector Store**: ChromaDB ✅
- **Embeddings**: fastembed `BAAI/bge-small-en-v1.5` (local, free); OpenAI optional via `AKASHA_EMBEDDING_BACKEND=openai` ✅
- **File Watching**: watchdog ✅
- **Testing**: pytest + real vault subset

---

## Phase 3: Extended Clients

**Timeline**: 3-4 weeks  
**Status**: ⚪ Not Started  
**Prerequisites**: Phase 2 API stable and in daily use

### Goals
- Build richer Raycast extension (TypeScript)
- Add VS Code extension for in-editor search
- Create CLI tool for terminal workflow
- Optional: Simple web UI for browsing

### Milestones

#### 3.1: Full Raycast Extension (Week 1-2)
- [ ] TypeScript Raycast extension scaffold
- [ ] Live search as you type
- [ ] Result preview with syntax highlighting
- [ ] Quick actions (open, copy path, copy content)
- [ ] Keyboard shortcuts for navigation
- [ ] Settings panel for API configuration

#### 3.2: VS Code Extension (Week 2-3)
- [ ] Extension scaffold with VS Code API
- [ ] Search command in command palette
- [ ] Results in sidebar panel
- [ ] Inline search with current file context
- [ ] Jump to note in Obsidian action

#### 3.3: CLI Tool (Week 3)
- [ ] Click/Typer-based CLI
- [ ] `akasha search "query"` command
- [ ] `akasha add` for quick note creation
- [ ] `akasha config` for settings
- [ ] Shell completion scripts

#### 3.4: Web UI (Week 4, Optional)
- [ ] Simple React or vanilla JS interface
- [ ] Browse all notes
- [ ] Search with filters (date, tags)
- [ ] Note preview and edit (opens Obsidian)
- [ ] Knowledge graph visualization

### Deliverables
- Published Raycast extension
- VS Code extension (marketplace or local)
- CLI tool with install script
- Optional: Hosted web UI for browsing

---

## Phase 4: Intelligence & Automation

**Timeline**: 4-6 weeks  
**Status**: ⚪ Not Started  
**Prerequisites**: Daily use of Phase 3 clients, validated need for features

### Goals
- Automatic semantic linking between notes
- Smart note suggestions based on current work
- Automated categorization and tagging
- Knowledge graph visualization

### Potential Features
- [ ] Automatic backlink suggestions
- [ ] Topic clustering and visualization
- [ ] "Similar notes" recommendations
- [ ] Periodic "what you wrote about this week" summaries
- [ ] Spaced repetition for important concepts
- [ ] Integration with calendar for temporal context
- [ ] Multi-modal support (images, PDFs)

### Research Required
- Graph algorithms for link discovery
- LLM-based summarization vs. embedding-based
- Privacy implications of automated analysis
- User control vs. automatic behavior

---

## Phase 5: Collaboration & Sharing (Future)

**Timeline**: TBD  
**Status**: ⚪ Not Started

### Potential Features
- Share specific notes or collections
- Collaborative note editing
- Team knowledge base
- Public/private note distinction
- Export to different formats

### Considerations
- Multi-tenancy in API
- Authentication and authorization
- Data privacy and encryption
- Sync conflicts resolution

---

## Ongoing Tasks (All Phases)

### Maintenance
- [ ] Regular dependency updates
- [ ] Security patches
- [ ] Performance monitoring
- [ ] Bug fixes based on usage

### Documentation
- [ ] Keep README up to date
- [ ] Document new features
- [ ] Create video tutorials
- [ ] Write blog posts about learnings

### Community
- [ ] Open source repository (if desired)
- [ ] Issue tracking and management
- [ ] Feature requests prioritization
- [ ] Contributions guidelines

---

## Decision Points

### After Phase 1
**Go/No-Go**: Does semantic search improve workflow enough to justify custom development?
- **Go**: Proceed to Phase 2
- **No-Go**: Stick with Obsidian + plugins, close project or pivot

### After Phase 2
**Investment**: Is the API providing value over Smart Connections?
- **High Value**: Invest in Phase 3 clients
- **Marginal**: Maintain but don't expand
- **Low Value**: Roll back, document learnings

### After Phase 3
**Scope**: What advanced features actually matter?
- Use data: Which clients get used most?
- User feedback: What's missing?
- Resource constraints: Time vs. impact

---

## Success Criteria

### Phase 1
- ✅ Using search 5+ times per week
- ✅ Clear limitations documented
- ✅ Confident custom API will help

### Phase 2
- ✅ API search faster than opening Obsidian
- ✅ Results quality ≥ Smart Connections
- ✅ Using custom search daily

### Phase 3
- ✅ One client becomes primary search method
- ✅ Search doesn't break flow
- ✅ Friends/colleagues interested in using it

### Phase 4+
- ✅ Automatic features save measurable time
- ✅ Knowledge graph provides insights
- ✅ System evolves with your work

---

## Anti-Goals

Things Akasha explicitly will NOT do:

- ❌ Replace Obsidian for note editing
- ❌ Become a full project management tool
- ❌ Require complex setup or configuration
- ❌ Lock users into proprietary formats
- ❌ Collect telemetry or usage data
- ❌ Require constant internet connection
- ❌ Become a social network for notes

---

## Resources Required

### Phase 1
- Time: 1-2 hours setup, daily usage
- Cost: $0 (or $8/mo for Readwise if desired)

### Phase 2
- Time: 40-60 hours development
- Cost: OpenAI API ~$5-10/mo for embeddings
- Infrastructure: Local development only

### Phase 3
- Time: 30-40 hours development
- Cost: Same as Phase 2
- Skills: TypeScript (Raycast, VS Code extensions)

### Phase 4+
- Time: TBD based on features
- Cost: May increase with usage
- Infrastructure: Possible cloud hosting for web UI

---

## Version History

### v0.1.0 (Current)
- Initial project setup
- Documentation created
- Phase 1 ready to begin

### Future Versions
- v0.2.0: Phase 1 complete, decision made
- v0.3.0: Basic API functional
- v0.4.0: Raycast integration working
- v1.0.0: Daily use, stable API
- v2.0.0: Multiple clients, advanced features

---

## Questions to Answer Along the Way

- [ ] Is ChromaDB sufficient or should we migrate to pgvector/Pinecone?
- [ ] Should we support multiple embedding models?
- [ ] Is context-awareness actually useful or just complexity?
- [ ] CLI vs. GUI: which gets more use?
- [ ] Should notes be chunked for long documents?
- [ ] How to handle images and PDFs in semantic search?
- [ ] Is there value in automatic summarization?
- [ ] Should we build mobile apps?

---

## Related Projects for Inspiration

- **Obsidian**: Note-taking foundation
- **Mem.ai**: Auto-linking and retrieval
- **Notion AI**: In-app AI features
- **Roam Research**: Bidirectional linking
- **Logseq**: Local-first knowledge base
- **Athens Research**: Open-source Roam alternative
- **Zotero**: Reference management with notes

---

*Last Updated: 2025-01-04*
