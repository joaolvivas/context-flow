# 🧠 Memory Router Proxy

> **Self-hosted Memory Router for LLMs** - Free alternative to Supermemory ($20/month)

A transparent LLM proxy that automatically enriches your conversations with relevant memories from past interactions. Built with **Python/FastAPI** + **Graphiti MCP** + **Neo4j**.

## ✨ Why This Exists

Instead of paying $20/month for Supermemory, get **the same features (+ more)** for **$0** with full control over your data.

## 🎯 What It Does

```
Your App → Memory Router Proxy → LLM Provider
              ↓
         Graphiti + Neo4j
         (Your Memory)
```

**Automatic workflow:**
1. Intercepts LLM requests
2. Searches your knowledge graph for relevant context
3. Enriches prompts with memories
4. Forwards to LLM (OpenAI, Anthropic, etc.)
5. Stores new memories asynchronously

**Zero code changes required** - Just change your base URL!

## 🚀 Quick Start

```bash
cd python-proxy

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
python main.py
```

**Full documentation:** See [`python-proxy/README.md`](python-proxy/README.md)

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [**README.md**](python-proxy/README.md) | Complete overview & features |
| [**USAGE_GUIDE.md**](python-proxy/USAGE_GUIDE.md) | Implementation guide (Python, TypeScript, cURL, Msty) |
| [**MCP_SETUP_GUIDE.md**](python-proxy/MCP_SETUP_GUIDE.md) | Setup Graphiti MCP + Neo4j |
| [**COMPARISON.md**](COMPARISON.md) | vs Supermemory feature comparison |

## 🏆 Feature Comparison

| Feature | Supermemory | This Proxy |
|---------|-------------|------------|
| **Memory Management** | ✅ Vector | ✅ **Graph** 🏆 |
| **Conversation Tracking** | ✅ | ✅ |
| **Intelligent Chunking** | ✅ | ✅ |
| **Token Optimization** | ✅ | ✅ |
| **Diagnostic Headers** | 7 | **10** 🏆 |
| **Entity Extraction** | ❌ | ✅ 🏆 |
| **Self-Hosted** | ❌ | ✅ 🏆 |
| **Cost/Year** | $240 | **$0** 🏆 |

**Full comparison:** [COMPARISON.md](COMPARISON.md)

## 💡 Use Cases

### With Msty Studio

1. Add custom provider in Msty:
   - **Base URL**: `http://localhost:8000/v1`
   - **API Key**: Your actual LLM provider key
2. Chat normally - memory is automatic!

### In Your App

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_KEY",
    base_url="http://localhost:8000/v1",
    default_headers={"X-User-Id": "alice"}
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

**More examples:** [USAGE_GUIDE.md](python-proxy/USAGE_GUIDE.md)

## 🎁 What You Get

✅ **Feature parity** with Supermemory $20/month tier
✅ **Superior memory** (Graph DB > Vector search)
✅ **$0 cost** (self-hosted forever)
✅ **100% privacy** (your data, your infrastructure)
✅ **Full control** (open source, customize anything)
✅ **10 diagnostic headers** (vs 7 from Supermemory)
✅ **Entity extraction** (Graphiti builds knowledge graph)
✅ **Relationship tracking** (Neo4j graph queries)

## 📦 Project Structure

```
proxy-orchestrator/
├── python-proxy/              # Main implementation
│   ├── main.py               # FastAPI server
│   ├── modules/
│   │   ├── router.py         # Memory routing logic
│   │   ├── token_counter.py  # Token counting
│   │   └── chunking.py       # Intelligent chunking
│   ├── models/               # Pydantic models
│   ├── utils/                # Logger, metrics
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Configuration template
│   ├── README.md             # Full documentation
│   ├── USAGE_GUIDE.md        # Implementation guide
│   └── MCP_SETUP_GUIDE.md    # Graphiti setup
└── COMPARISON.md             # vs Supermemory comparison
```

## 🛠️ Tech Stack

- **Python 3.9+** + FastAPI
- **Graphiti** - Knowledge graph memory
- **Neo4j** - Graph database
- **tiktoken** - Token counting
- **OpenAI/Anthropic/etc** - LLM providers

## 🔧 Configuration

**Minimal `.env`:**
```bash
# Server
PORT=8000

# MCP Endpoints
MCP_SEARCH_ENDPOINT=http://localhost:5000/mcp/search
MCP_STORE_ENDPOINT=http://localhost:5000/mcp/store

# Memory
MEMORY_ENABLED=true
MEMORY_MAX_CONTEXT_TOKENS=2000
```

**Full config:** See [python-proxy/.env.example](python-proxy/.env.example)

## 📊 Diagnostic Headers

Every response includes detailed metrics:

```http
X-Memory-Conversation-Id: 550e8400-e29b-41d4-a716-446655440000
X-Memory-Chunks-Retrieved: 3
X-Memory-Chunks-Created: 2
X-Memory-Tokens-Input: 450
X-Memory-Tokens-Output: 320
X-Memory-Tokens-Memory: 180
X-Memory-Tokens-Processed: 950
X-Memory-Processing-Time-Ms: 145
```

## 🎯 Next Steps

1. **Read the guides:**
   - [python-proxy/README.md](python-proxy/README.md) - Overview
   - [python-proxy/USAGE_GUIDE.md](python-proxy/USAGE_GUIDE.md) - How to use
   - [python-proxy/MCP_SETUP_GUIDE.md](python-proxy/MCP_SETUP_GUIDE.md) - Setup Graphiti

2. **Setup infrastructure:**
   - Install Neo4j (Docker recommended)
   - Setup Graphiti MCP server
   - Configure Memory Router Proxy

3. **Start using:**
   - Point Msty Studio to `http://localhost:8000/v1`
   - Or integrate via OpenAI SDK

## 🙏 Credits

- **Graphiti** - Graph-based memory layer
- **Supermemory** - Inspiration for the Memory Router pattern
- **MCP** - Model Context Protocol standard

## 📄 License

MIT

---

**Built to prove you don't need $240/year for good memory.** 🧠💰

Get started: [`python-proxy/README.md`](python-proxy/README.md)
