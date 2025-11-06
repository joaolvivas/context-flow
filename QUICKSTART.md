# ⚡ ContextFlow - Quick Start Guide

**One unified 3-tier memory system. Zero manual calls. 77% cost reduction.**

---

## 🚀 30-Second Setup

### Prerequisites
- Python 3.9+
- Redis (`brew install redis` on Mac)
- Neo4j AuraDB account (free tier available)
- OpenAI API key

### Installation

```bash
# 1. Clone and setup
git clone https://github.com/joaolvivas/proxy-orchestrator
cd proxy-orchestrator

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   - OPENAI_API_KEY
#   - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# 3. Start the system
./start_memory_system.sh
```

**That's it!** Your unified 3-tier memory system is running on `http://localhost:8000`

---

## 🧠 What You Get

### Unified 3-Tier Architecture
All tiers work together automatically - you don't manage them separately:

1. **Tier 1: Working Memory** (Redis)
   - Stores last 10 conversation turns
   - <1ms latency, zero cost
   - Handles 90% of queries

2. **Tier 2: Session Facts** (Redis)
   - AI-extracted key information
   - ~5ms latency, minimal cost
   - Handles 8% of queries

3. **Tier 3: Knowledge Graph** (Neo4j + Graphiti)
   - Long-term relationships and entities
   - ~500ms latency, scales infinitely
   - Handles 2% of queries (deep context)

**Progressive Injection:** System automatically decides which tiers to use based on query complexity.

---

## 🔌 Usage

### With IDEs (Cursor, VS Code, Windsurf)

1. Open Settings → Models
2. Set Base URL: `http://localhost:8000/v1`
3. Add your OpenAI API key
4. Code normally - memory flows automatically! ⚡

### With CLI Tools (Aider, Claude Code)

```bash
# Aider
aider --openai-api-base http://localhost:8000/v1

# Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8000/v1
claude-code
```

### With Python/Node.js

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-key",
    base_url="http://localhost:8000/v1"  # 👈 One line change
)

# First conversation
client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "My name is Alice"}]
)
# ⚡ Saved to all 3 tiers automatically

# Later conversation (different session)
client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What's my name?"}]
)
# ⚡ Retrieved from appropriate tier automatically
# Returns: "Your name is Alice!" 🎉
```

**Zero manual calls. Zero memory management. Just works.**

---

## 📊 Verification

```bash
# Check system health
curl http://localhost:8000/health

# Expected response:
{
  "status": "ok",
  "memory": {
    "enabled": true
  },
  "components": {
    "memory": true
  }
}

# Check Neo4j connection
curl http://localhost:5001/health

# Expected response:
{
  "status": "healthy",
  "neo4j": "connected",
  "graphiti": "initialized"
}

# Test memory flow
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Remember: my favorite color is blue"}]
  }'

# Wait 5 seconds for async processing, then recall
sleep 5

curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "What is my favorite color?"}]
  }'
# Should return: "Your favorite color is blue" ✅
```

---

## 📈 What Makes This Different?

### Traditional Approach
```
❌ Manual memory management:
   memory.save_episode(...)
   memory.search(...)
   memory.delete_episode(...)

❌ Separate solutions:
   - Redis for cache
   - Vector DB for embeddings
   - Graph DB for relationships
   - You wire them together

❌ Easy to forget to save
❌ Complex integration code
```

### ContextFlow (Unified System)
```
✅ Automatic memory flow:
   Just chat normally
   
✅ One integrated system:
   - All 3 tiers work together
   - Automatic tier selection
   - Unified management

✅ Impossible to forget
✅ Zero integration code
```

---

## 🎯 Key Features

- ⚡ **Automatic Memory:** Saves & retrieves without any manual calls
- 🧠 **Intelligent Routing:** System picks the right tier(s) for each query
- 🎯 **77% Token Reduction:** Progressive injection based on query complexity
- 🚀 **<120ms Response Time:** 6.7x faster than traditional RAG
- 🔒 **Self-Hosted:** Your data stays on your infrastructure
- 💰 **$0 Forever:** No subscriptions, no vendor lock-in
- 🔌 **Universal:** Works with any tool that allows custom endpoints

---

## 📊 Monitoring

```bash
# Watch proxy logs (all tiers)
tail -f /tmp/proxy_v3.log

# Watch Graphiti/Neo4j logs
tail -f /tmp/http_wrapper.log

# Check Redis
redis-cli INFO
redis-cli KEYS "*"

# Query Neo4j directly (via Graphiti wrapper)
curl -X POST http://localhost:5001/mcp/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does the user work on?",
    "user_id": "lucas-ai",
    "group_id": "lucas-ai",
    "limit": 5
  }'
```

---

## 🛠️ Configuration

All settings in `.env`:

```bash
# Required
OPENAI_API_KEY=sk-...

# Neo4j (Tier 3)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Memory Settings
MEMORY_ENABLED=true
MEMORY_BACKEND=graphiti
WORKING_MEMORY_TURNS=10

# Progressive Injection
PROGRESSIVE_INJECTION=true
```

See `.env.example` for all options.

---

## 🐛 Troubleshooting

### Services won't start
```bash
# Check if ports are in use
lsof -i :8000  # Proxy
lsof -i :5001  # Graphiti
lsof -i :6379  # Redis

# Kill processes if needed
kill -9 $(lsof -ti :8000)

# Restart
./start_memory_system.sh
```

### Memory not being recalled
```bash
# 1. Verify Neo4j connection
curl http://localhost:5001/health

# 2. Check if data was stored (after chatting)
curl -X POST http://localhost:5001/mcp/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "user_id": "lucas-ai", "group_id": "lucas-ai", "limit": 5}'

# 3. Check proxy logs
tail -f /tmp/proxy_v3.log | grep -i "tier"
```

### High latency
```bash
# Check which tiers are being used
tail -f /tmp/proxy_v3.log | grep "tiers_used"

# Most queries should use only Tier 1 or 1+2
# Only deep queries should use all 3 tiers
```

---

## 📚 Next Steps

- Read [README.md](README.md) for full documentation
- Check [AGENTS.md](AGENTS.md) for project structure
- See examples in `examples/` directory
- Join discussions on GitHub

---

## 💡 Pro Tips

1. **Use descriptive user IDs** via `X-User-Id` header for multi-user systems
2. **Monitor the diagnostic headers** in responses to understand tier usage
3. **Tier 3 is async** - give it 5-10 seconds after storing before expecting recall
4. **Progressive injection saves 77%** - trust the system to pick the right amount of context
5. **Self-hosted means free** - no usage limits, no subscriptions, ever

---

**Made with ⚡ by developers who believe in open source and self-hosting.**

Questions? Issues? → [GitHub Issues](https://github.com/joaolvivas/proxy-orchestrator/issues)
