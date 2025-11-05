# MemoryStack Documentation

Complete documentation for MemoryStack - The Open-Source Intelligence Layer for LLM Memory.

---

## 🚀 Quick Links

- **[Getting Started](#getting-started)** - New to MemoryStack? Start here
- **[Installation](#installation)** - How to install and configure
- **[Architecture](#architecture)** - How it works under the hood
- **[API Reference](#api-reference)** - Complete API documentation
- **[Backends](#backends)** - Setup guides for different backends
- **[Examples](#examples)** - Code examples and integrations
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions

---

## Getting Started

### What is MemoryStack?

MemoryStack is an intelligent proxy that sits between your application and LLM provider, automatically managing memory across conversations. It reduces token costs by 77% while giving your AI perfect recall.

### Why Use MemoryStack?

- **77% cost reduction** through progressive context injection
- **Perfect memory** across all conversations
- **Backend agnostic** - works with any memory store
- **Zero code changes** - just change your base URL
- **Production ready** - battle-tested with Msty Studio

### Quick Start (30 seconds)

```bash
# Clone and start
git clone https://github.com/joaolvivas/memorystack
cd memorystack
docker-compose up -d

# Test
curl http://localhost:8000/health
```

[Full Quick Start Guide →](../README.md#-try-it-now-30-seconds)

---

## Installation

### Docker (Recommended)

**Simplest Setup (Supermemory backend):**
```bash
# 1. Copy and edit .env
cp .env.example .env
# Edit: Add OPENAI_API_KEY and SUPERMEMORY_API_KEY

# 2. Start
docker-compose up -d

# Done!
```

**Graphiti Setup (Graph-based memory):**
```bash
# 1. Copy and edit .env
cp .env.example .env
# Edit: Add OPENAI_API_KEY, NEO4J_URI, NEO4J_PASSWORD

# 2. Start with Graphiti profile
docker-compose --profile graphiti up -d

# Done!
```

### Manual Installation

```bash
# 1. Clone
git clone https://github.com/joaolvivas/memorystack
cd memorystack

# 2. Run installer
./install.sh

# 3. Start
python -m uvicorn src.memorystack.main:app --host 0.0.0.0 --port 8000
```

[Detailed Installation Guide →](../README.md#-try-it-now-30-seconds)

---

## Architecture

### 3-Tier Memory System

MemoryStack uses a hierarchical memory architecture inspired by human memory:

```
Tier 1: Working Memory (Redis)
├─ Recent conversation (last 10-20 turns)
├─ Retrieval: <1ms
├─ Cost: Zero (just storage)
└─ Always used

Tier 2: Session Memory (Redis + GPT-4o-mini)
├─ Extracted facts (key information)
├─ Retrieval: ~5ms
├─ Cost: ~100 tokens
└─ Used for factual queries (98%)

Tier 3: Long-term Memory (Your Choice)
├─ Graph/Vector database
├─ Retrieval: ~500ms
├─ Cost: 500-2000 tokens
└─ Used for deep queries (2%)
```

### Progressive Injection

Instead of injecting all context for every query, MemoryStack intelligently selects the right amount:

| Query Type | Example | Tiers Used | Tokens | Frequency |
|------------|---------|------------|--------|-----------|
| **Level 1** | "Hello" | Tier 1 only | 200 | 90% |
| **Level 2** | "What's my name?" | Tier 1+2 | 400 | 8% |
| **Level 3** | "Tell me everything" | All tiers | 1000 | 2% |

**Result**: 232 tokens average (vs 1000 before) = **77% reduction**

[Deep Dive: Progressive Injection →](progressive-injection.md)

### Query Flow

```
1. User Query
    ↓
2. Query Classification (regex patterns)
    ├─ Simple → Level 1
    ├─ Factual → Level 2
    └─ Deep → Level 3
    ↓
3. Memory Retrieval (appropriate tiers)
    ↓
4. Context Injection
    ↓
5. Forward to LLM
    ↓
6. Response
    ↓
7. Background Storage (all tiers)
```

---

## API Reference

### Endpoints

#### `POST /chat/completions`
#### `POST /v1/chat/completions`

OpenAI-compatible chat completion endpoint.

**Request:**
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "What's my name?"}
  ],
  "memory_enabled": true,  // Optional: disable memory
  "conversation_id": "custom-id"  // Optional: custom conversation ID
}
```

**Response:**
Standard OpenAI response plus diagnostic headers:

```
X-Memory-Conversation-Id: default-alice
X-Memory-Tiers-Used: working_memory,session_facts
X-Memory-Tier1-Turns: 10
X-Memory-Tier2-Facts: 3
X-Memory-Tier3-Memories: 0
X-Memory-Tokens-Input: 25
X-Memory-Tokens-Output: 45
X-Memory-Tokens-Memory: 300
X-Memory-Cost-Estimate: 370
X-Memory-Processing-Time-Ms: 125
X-Memory-Cache-Hit: false
X-Memory-Profile-Found: true
```

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-11-05T...",
  "components": {
    "memory": true
  }
}
```

### Headers

**Request Headers:**
- `Authorization: Bearer sk-...` - LLM provider API key (required)
- `X-User-Id: alice` - User identifier for memory namespace (optional)
- `X-Provider-URL: https://api.openai.com/v1` - Override default provider (optional)

**Response Headers:**
- `X-Memory-*` - 11 diagnostic headers (see above)

[Full API Documentation →](usage-guide.md)

---

## Backends

MemoryStack works with any memory backend through a pluggable adapter system.

### Supported Backends

#### Graphiti + Neo4j (Graph-based)
- **Best for**: Relationships, entity tracking, complex queries
- **Setup**: [Graphiti Setup Guide →](graphiti-setup.md)
- **Pros**: Rich relationships, entity extraction, long-term memory
- **Cons**: Requires Neo4j instance, slower queries (~500ms)

#### Supermemory (Vector-based)
- **Best for**: Simple setup, semantic search, personal AI
- **Setup**: Just add `SUPERMEMORY_API_KEY` to `.env`
- **Pros**: Fast, cloud-hosted, easy setup
- **Cons**: $20/month for cloud, or self-host

#### Pinecone (Coming Soon)
- Scalable vector database
- Enterprise-ready

#### Custom Backend
- Implement your own adapter
- See: `src/memorystack/backends/base.py`

[Backend Comparison →](../README.md#-backend-agnostic)

---

## Examples

### Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-...",
    base_url="http://localhost:8000/v1",
    default_headers={"X-User-Id": "alice"}
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

[More Python Examples →](../examples/python/)

### Node.js

```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  apiKey: 'sk-...',
  baseURL: 'http://localhost:8000/v1',
  defaultHeaders: {'X-User-Id': 'bob'}
});

const response = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{role: 'user', content: 'Hello!'}]
});
```

[More Node.js Examples →](../examples/nodejs/)

### cURL

```bash
curl -X POST http://localhost:8000/chat/completions \
  -H "Authorization: Bearer sk-..." \
  -H "X-User-Id: charlie" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'
```

[More cURL Examples →](../examples/curl/)

### Integrations

- **[Msty Studio](../examples/integrations/msty_setup.md)** - Desktop AI chat app
- **LangChain** - Coming soon
- **LlamaIndex** - Coming soon

---

## Troubleshooting

### Common Issues

#### Memory Not Working

**Symptoms**: AI doesn't remember previous conversations

**Solutions**:
1. Check Redis is running: `redis-cli ping`
2. Check logs: `docker logs memorystack-proxy`
3. Verify conversation IDs are stable (not random)
4. Check `X-Memory-*` headers in responses

[Full Troubleshooting Guide →](troubleshooting.md)

#### Slow Responses

**Symptoms**: Queries taking >1 second

**Solutions**:
1. Check which tiers are being used (`X-Memory-Tiers-Used`)
2. Reduce `WORKING_MEMORY_TURNS` (default: 10)
3. Disable Tier 3 if not needed: `GRAPHITI_ENABLED=false`
4. Check Redis latency: `redis-cli --latency`

#### High Token Costs

**Symptoms**: Not seeing 77% reduction

**Solutions**:
1. Enable progressive injection: `PROGRESSIVE_INJECTION=true`
2. Check query classification is working
3. Review `X-Memory-Cost-Estimate` headers
4. Ensure cache is enabled: `CACHE_ENABLED=true`

---

## Configuration

### Environment Variables

**Required:**
```bash
OPENAI_API_KEY=sk-...  # For Tier 2 fact extraction
```

**Redis (Tier 1 & 2):**
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
WORKING_MEMORY_TURNS=10  # Optimized default
WORKING_MEMORY_TTL=1800  # 30 minutes
SESSION_MEMORY_MODEL=gpt-4o-mini
SESSION_MEMORY_TTL=86400  # 24 hours
```

**Backend Selection:**
```bash
MEMORY_BACKEND=graphiti  # or supermemory

# If graphiti:
GRAPHITI_URL=http://localhost:5000
NEO4J_URI=neo4j+s://...
NEO4J_PASSWORD=...

# If supermemory:
SUPERMEMORY_API_KEY=...
```

**Features:**
```bash
CACHE_ENABLED=true
PROFILE_ENABLED=true
PROGRESSIVE_INJECTION=true
```

[Full Configuration Reference →](../. env.example)

---

## Performance

### Benchmarks (Real Production Data)

**Query Response Times:**
- Tier 1 only (90%): 80ms
- Tier 1+2 (8%): 180ms
- All tiers (2%): 480ms
- **Average: 120ms**

**Token Usage:**
- Before: 1000 tokens/query average
- After: 232 tokens/query average
- **Reduction: 77%**

**Cost Savings (100K queries/month):**
- Before: $15/month
- After: $3/month
- **Saved: $12/month (80%)**

Scale to 1M queries: **$120/month saved**

[Performance Deep Dive →](progressive-injection.md)

---

## Contributing

We welcome contributions! See:
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute
- **[Code of Conduct](../CONTRIBUTING.md#code-of-conduct)** - Community standards
- **[Roadmap](../README.md#-roadmap)** - Planned features

---

## Support

- 💬 [GitHub Discussions](https://github.com/joaolvivas/memorystack/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/joaolvivas/memorystack/issues) - Report bugs
- 📖 [Documentation](.) - You are here!
- ⭐ [Star on GitHub](https://github.com/joaolvivas/memorystack) - Show support

---

## License

MemoryStack is open source under the [MIT License](../LICENSE).

**You're free to:**
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Use privately

---

<div align="center">

**Built to prove you don't need $240/year for good memory.** 🧠💰

[Get Started](../README.md#-try-it-now-30-seconds) • [Examples](../examples/) • [GitHub](https://github.com/joaolvivas/memorystack)

</div>
