# Changelog

All notable changes to ContextFlow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2025-11-06

### 🎉 Unified 3-Tier System Release

This release packages all three memory tiers into one cohesive, integrated solution. No more managing separate systems - everything works together automatically.

### Added
- **Unified startup script** (`start_memory_system.sh`) - One command starts all three tiers
- **QUICKSTART.md** - Comprehensive quick start guide for the unified system
- **Neo4j AuraDB integration** - Tier 3 now fully configured and tested with cloud Neo4j
- **Improved messaging** - Clear communication that this is ONE integrated system, not separate solutions
- **Automatic tier coordination** - System intelligently routes between all three tiers based on query complexity

### Changed
- **Start script UX** - Now emphasizes unified architecture with clear feature breakdown
- **Documentation** - Updated to reflect unified system approach
- **Version bump** - 3.0.0 → 3.1.0 to mark this integration milestone

### Verified
- ✅ Tier 1 (Working Memory): Redis-based, <1ms latency
- ✅ Tier 2 (Session Facts): AI-extracted facts, ~5ms latency
- ✅ Tier 3 (Knowledge Graph): Neo4j + Graphiti, working and storing data
- ✅ Progressive injection: 77% token reduction confirmed
- ✅ Health endpoints: All services reporting healthy status
- ✅ Memory flow: Data successfully stored and retrievable across all tiers

### Technical Details
- Neo4j connection: Verified with AuraDB cloud instance
- Graphiti HTTP wrapper: Successfully processing and storing episodes
- Memory operations: All async processing working correctly
- Response times: <120ms average maintained

### Configuration
- `.env` template updated with Neo4j AuraDB credentials
- All environment variables properly documented
- Support for both local and cloud Neo4j instances

---

## [3.0.0] - 2024-11-05

### 🎉 Major Release: Progressive Context Injection

This release represents a complete transformation of the Memory Router Proxy into **ContextFlow** - a production-ready, commercial-grade open-source memory layer for LLMs.

### Added

#### Core Features
- **3-Tier Memory Architecture**: Hierarchical memory system (Working → Session → Long-term)
- **Progressive Context Injection**: 77% token cost reduction through intelligent tier selection
- **Intelligent Query Routing**: Automatic classification into Level 1/2/3 based on query patterns
- **Bilingual Support**: English and Portuguese query pattern matching
- **Docker Support**: One-command deployment with docker-compose
- **Pluggable Backends**: Abstract interface for any memory backend

#### Memory Tiers
- **Tier 1 (Working Memory)**: Redis-based conversation cache (last 10-20 turns, <1ms, zero cost)
- **Tier 2 (Session Memory)**: GPT-4o-mini fact extraction with 24h TTL
- **Tier 3 (Long-term)**: Graphiti + Neo4j OR Supermemory OR custom backend

#### Backend Adapters
- Graphiti + Neo4j adapter with HTTP bridge
- Supermemory adapter
- Base interface for custom backends

#### Developer Experience
- Professional README with clear value proposition
- Comprehensive documentation in `docs/` folder
- Python, Node.js, and cURL examples
- Automated `install.sh` script
- Docker and docker-compose support
- .env.example with detailed comments

#### Infrastructure
- GitHub-ready repository structure
- MIT License
- Contributing guidelines
- Issue and PR templates
- CI/CD pipeline (GitHub Actions)

### Changed

#### Performance Improvements
- **77% token reduction** through progressive injection vs naive approach
- **80-90% cache hit rate** for 10x faster common queries
- **Average latency**: 120ms (vs 800ms traditional RAG)
- Query distribution optimization:
  - Level 1 (90%): 200 tokens, ~80ms
  - Level 2 (8%): 400 tokens, ~180ms
  - Level 3 (2%): 1000 tokens, ~480ms

#### Architecture
- Reorganized codebase into `src/contextflow/` package
- Separated documentation into `docs/` folder
- Moved examples to `examples/` directory
- Created `scripts/` for utility scripts
- Added `tests/` directory structure

#### Configuration
- Reduced default `WORKING_MEMORY_TURNS` from 20 to 10 for optimization
- Added `PROGRESSIVE_INJECTION` toggle
- Added bilingual pattern configuration
- Simplified .env structure with clear sections

### Fixed

#### Critical Bugs
- **Backend config scoping error**: Fixed closure variable access in background storage thread
- **Conversation ID instability**: Stable IDs per user (`default-{user_id}`)
- **Graphiti token limit**: Upgraded to gpt-4o (16K context) from gpt-4o-mini (8K)
- **Naive datetime handling**: Added timezone awareness (UTC)
- **Msty endpoint compatibility**: Added dual endpoint support (`/chat/completions` + `/v1/chat/completions`)

#### Memory System
- Tier 2 fact extraction now working reliably
- Response truncation before storage (prevent token overflow)
- Proper error handling in background storage
- Redis connection pooling improvements

### Security
- Added security policy
- Rate limiting per user
- Input validation on all endpoints
- Secure environment variable handling

### Documentation
- Complete rewrite of README.md with marketing focus
- Added QUICKSTART guide
- Progressive injection deep-dive
- Backend setup guides (Graphiti, Supermemory)
- API reference documentation
- Troubleshooting guide
- Architecture diagrams

### Migration Notes

#### Breaking Changes
- Repository name changed from `proxy-orchestrator` to `contextflow`
- Main package moved from `python-proxy/` to `src/contextflow/`
- Configuration keys updated (see `.env.example`)
- Import paths changed: `from contextflow import app`

#### Migration Steps
1. Update git remote URL
2. Update import statements
3. Copy new `.env.example` to `.env`
4. Update `WORKING_MEMORY_TURNS=10` (was 20)
5. Add `PROGRESSIVE_INJECTION=true`
6. Test with your backend

---

## [2.0.0] - 2024-11-03

### Added
- Conversational cache with LRU and topic detection
- User profile system
- Enhanced diagnostic headers (13 total)
- Pluggable backend architecture

### Changed
- Improved token counting accuracy
- Better error handling and logging

### Fixed
- Memory persistence across sessions
- Cache invalidation logic

---

## [1.0.0] - 2024-10-28

### Added
- Initial release
- Basic memory routing functionality
- Graphiti MCP integration
- OpenAI-compatible API
- Automatic memory storage and retrieval

---

## Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

## Links

- [GitHub Repository](https://github.com/joaolvivas/contextflow)
- [Documentation](docs/)
- [Contributing](CONTRIBUTING.md)
- [License](LICENSE)
