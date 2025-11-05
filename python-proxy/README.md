# Memory Router Proxy

> Transparent LLM proxy with automatic memory management, inspired by Supermemory

A simple Python/FastAPI proxy that sits between Msty Studio (or any OpenAI-compatible client) and your LLM provider, automatically enriching conversations with relevant context from past interactions.

## Features

- ✅ **OpenAI-compatible API** - Drop-in replacement, just change the base URL
- ✅ **Automatic Memory** - Searches and injects relevant past context
- ✅ **Transparent Operation** - Works without code changes in your client
- ✅ **Graceful Fallback** - If memory fails, requests pass through normally
- ✅ **Async Storage** - Memories stored without blocking responses
- ✅ **Multi-Provider** - Works with OpenAI, Anthropic, Groq, etc.
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

Diagnostic headers:

```
X-Memory-Chunks-Retrieved: 3
X-Memory-Context-Modified: true
X-Memory-Processing-Time-Ms: 145
```

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
```

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
│   └── router.py        # Memory routing logic
│
├── models/
│   ├── request_models.py
│   └── response_models.py
│
└── utils/
    ├── logger.py        # Structured logging
    └── metrics.py       # Cost & usage tracking
```

## Troubleshooting

### Memory not working

The proxy works without MCP - it just won't have memory features. Check if MCP endpoints are reachable.

### Slow responses

Memory search has 1.5s timeout. If MCP is slow, increase timeout in `router.py`.

## Comparison to Supermemory

| Feature | Supermemory | This Proxy |
|---------|-------------|------------|
| Memory Management | ✅ Cloud | ✅ Local (MCP) |
| OpenAI Compatible | ✅ | ✅ |
| Self-Hosted | ❌ | ✅ |
| Multi-Provider | ✅ | ✅ |
| Cost | Paid after 100k tokens | Free (self-hosted) |

## License

MIT
