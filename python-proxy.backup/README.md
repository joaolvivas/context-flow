# Memory Router Proxy

> Transparent LLM proxy with automatic memory management, inspired by Supermemory

A simple Python/FastAPI proxy that sits between Msty Studio (or any OpenAI-compatible client) and your LLM provider, automatically enriching conversations with relevant context from past interactions.

## Features

### Core Memory Features (Supermemory-inspired)
- ✅ **OpenAI-compatible API** - Drop-in replacement, just change the base URL
- ✅ **Automatic Memory** - Searches and injects relevant past context
- ✅ **Intelligent Chunking** - Splits long messages into semantic chunks
- ✅ **Conversation Tracking** - Tracks multi-turn conversations with unique IDs
- ✅ **Token Optimization** - Prioritizes most relevant memories to save tokens
- ✅ **Transparent Operation** - Works without code changes in your client
- ✅ **Graceful Fallback** - If memory fails, requests pass through normally
- ✅ **Async Storage** - Memories stored without blocking responses

### Provider & Integration
- ✅ **Multi-Provider** - Works with OpenAI, Anthropic, Groq, DeepInfra, etc.
- ✅ **MCP/Graphiti Integration** - Graph-based memory with Neo4j
- ✅ **Automatic Entity Extraction** - Graphiti builds knowledge graph automatically

### Diagnostics & Monitoring
- ✅ **Rich Diagnostic Headers** - Complete visibility into memory operations
- ✅ **Token Counting** - Track input, output, and memory token usage
- ✅ **Metrics & Logging** - Track usage, costs, and memory effectiveness

## How It Works

```
Msty Studio → Memory Proxy → LLM Provider
              ↓
         MCP/Graphiti
         (Memory Storage)
```

1. **Intercept** - Proxy receives chat request
2. **Search** - Finds relevant memories from past conversations
3. **Enrich** - Injects context into the prompt
4. **Forward** - Sends enriched request to LLM
5. **Store** - Saves new memories asynchronously
6. **Return** - Streams response back to client

## Quick Start

### 1. Install Dependencies

```bash
cd python-proxy
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Minimal config needed in .env:
# - DEFAULT_PROVIDER_URL (default: https://api.openai.com/v1)
# - DEFAULT_MODEL (default: gpt-4o-mini)
# - MCP endpoints (if using MCP/Graphiti)
```

### 3. Run

```bash
python main.py
# Or: uvicorn main:app --reload --port 8000
```

### 4. Use with Msty Studio

In Msty, add a custom provider:
- **Name**: Memory Router
- **Base URL**: `http://localhost:8000/v1`
- **API Key**: Your actual LLM provider key (OpenAI, etc)

That's it! Now all conversations through this provider will have automatic memory.

## Usage

### Via Msty Studio

Just select the Memory Router provider and chat normally. The proxy will:
- Automatically search for relevant past context
- Inject it into your prompts
- Store new memories after each conversation

### Programmatic Usage

```python
from modules.router import route

response = route(
    prompt="What did we discuss yesterday?",
    user_id="user-123",
    api_key="sk-...",
    memory_enabled=True
)

print(response)
```

### API Headers

Optional headers:

```
Authorization: Bearer your-llm-provider-key
X-User-Id: unique-user-identifier
X-Provider-URL: https://api.openai.com/v1 (override default)
```

### Response Headers

Comprehensive diagnostic headers (matching Supermemory):

```
X-Memory-Conversation-Id: 550e8400-e29b-41d4-a716-446655440000
X-Memory-Context-Modified: true
X-Memory-Chunks-Retrieved: 3
X-Memory-Chunks-Created: 2
X-Memory-Tokens-Input: 450
X-Memory-Tokens-Output: 320
X-Memory-Tokens-Memory: 180
X-Memory-Tokens-Processed: 950
X-Memory-Processing-Time-Ms: 145
X-Memory-Error: <error message if any>
```

**What each header means:**
- `Conversation-Id`: Unique ID for tracking multi-turn conversations
- `Context-Modified`: Whether memory context was injected
- `Chunks-Retrieved`: Number of memory chunks added to context
- `Chunks-Created`: Number of chunks created when storing memory
- `Tokens-Input`: Tokens in original user messages
- `Tokens-Output`: Tokens in LLM response
- `Tokens-Memory`: Tokens used by memory context
- `Tokens-Processed`: Total tokens processed by LLM
- `Processing-Time-Ms`: Total processing time in milliseconds
- `Error`: Error message if memory operation failed (graceful degradation)

## Configuration

Edit `.env` file:

```bash
# Server
PORT=8000

# Default LLM provider
DEFAULT_PROVIDER_URL=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4o-mini

# MCP/Memory endpoints
MCP_SEARCH_ENDPOINT=http://localhost:5000/mcp/search
MCP_STORE_ENDPOINT=http://localhost:5000/mcp/store

# Memory settings
MEMORY_ENABLED=true
MEMORY_SEARCH_LIMIT=5

# Memory optimization (NEW)
MEMORY_MAX_CONTEXT_TOKENS=2000  # Max tokens for memory context
MEMORY_CHUNK_SIZE=500            # Chunk size for long messages
```

### Configuration Options Explained

**Memory Optimization Settings:**
- `MEMORY_MAX_CONTEXT_TOKENS`: Maximum tokens to use for memory context. Prevents exceeding model context windows. Higher values = more context but higher cost.
- `MEMORY_CHUNK_SIZE`: When storing long messages, they're split into semantic chunks of this size. Smaller chunks = better retrieval granularity.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Main chat endpoint (OpenAI-compatible) |
| `/health` | GET | Health check |
| `/metrics` | GET | Usage metrics and stats |
| `/` | GET | Service info |

## Memory Integration

### Using MCP/Graphiti

Configure endpoints in `.env`:

```bash
MCP_SEARCH_ENDPOINT=http://localhost:5000/mcp/search
MCP_STORE_ENDPOINT=http://localhost:5000/mcp/store
```

### Conversation Tracking

Track multi-turn conversations with `conversation_id`:

```json
{
  "model": "gpt-4o-mini",
  "messages": [...],
  "conversation_id": "my-conversation-123"
}
```

If not provided, a UUID is auto-generated. Use the same ID across messages to track conversation history.

### Disable Memory

Per-request:

```json
{
  "model": "gpt-4o-mini",
  "messages": [...],
  "memory_enabled": false
}
```

Globally in `.env`:

```bash
MEMORY_ENABLED=false
```

## Metrics

```bash
curl http://localhost:8000/metrics
```

Returns usage stats, costs, and memory effectiveness.

## Examples

See `example_usage.py`:

```bash
python example_usage.py
```

## Architecture

```
python-proxy/
├── main.py              # FastAPI server
├── config.py            # Configuration
├── requirements.txt     # Dependencies
│
├── modules/
│   ├── router.py        # Memory routing logic
│   ├── token_counter.py # Token counting (tiktoken)
│   └── chunking.py      # Intelligent chunking
│
├── models/
│   ├── request_models.py
│   └── response_models.py
│
└── utils/
    ├── logger.py        # Structured logging
    └── metrics.py       # Cost & usage tracking
```

### Key Components

**router.py** - Core memory routing with:
- `search_memories()` - Search for relevant memories via MCP
- `prioritize_memories()` - Token-aware memory filtering
- `chunk_text()` - Semantic chunking for long messages
- `enrich_messages()` - Inject memory context into prompts
- `store_memory_async()` - Async storage with chunking
- `memory_route()` - Main routing function

**token_counter.py** - Accurate token counting:
- Uses tiktoken for precise counts
- Supports multiple models (GPT-4, Claude, etc.)
- Counts message arrays and memory context
- Context window management

**chunking.py** - Intelligent text splitting:
- Semantic chunking by paragraphs/sentences
- Preserves code blocks
- Configurable chunk sizes
- Conversation-aware chunking

## Troubleshooting

### Memory not working

The proxy works without MCP - it just won't have memory features. Check if MCP endpoints are reachable.

### Slow responses

Memory search has 1.5s timeout. If MCP is slow, increase timeout in `router.py`.

## Comparison to Supermemory

| Feature | Supermemory | This Proxy |
|---------|-------------|------------|
| **Core Functionality** | | |
| Memory Management | ✅ Cloud/Vector | ✅ Local Graph (MCP/Graphiti) |
| OpenAI Compatible | ✅ | ✅ |
| Conversation Tracking | ✅ | ✅ |
| Intelligent Chunking | ✅ | ✅ |
| Token Optimization | ✅ | ✅ |
| Async Memory Storage | ✅ | ✅ |
| **Diagnostics** | | |
| Diagnostic Headers | ✅ | ✅ |
| Token Counting | ✅ | ✅ |
| Error Reporting | ✅ | ✅ |
| **Integration** | | |
| Self-Hosted | ❌ | ✅ |
| Multi-Provider | ✅ | ✅ |
| Graph-based Memory | ❌ | ✅ (Graphiti/Neo4j) |
| Entity Extraction | ❌ | ✅ (via Graphiti) |
| **Cost** | | |
| Pricing | $20/month | ✅ **FREE** (self-hosted) |

**Why this solution?**
- 🎯 **No vendor lock-in** - You own your data and infrastructure
- 💰 **Zero recurring costs** - Self-hosted means free forever
- 🧠 **Superior memory** - Graph-based memory (Graphiti) > vector search
- 🔗 **Automatic relationships** - Graphiti builds knowledge graphs automatically
- 🔒 **Privacy** - Your conversations stay on your infrastructure

## License

MIT
