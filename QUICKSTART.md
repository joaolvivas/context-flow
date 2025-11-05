# 🚀 Quick Start Guide

Get your Memory Router Proxy running in 5 minutes.

## Prerequisites

- Python 3.9+
- pip

## Installation

```bash
# 1. Clone repository
git clone <your-repo-url>
cd proxy-orchestrator/python-proxy

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
```

## Configuration

Edit `.env` file:

### Minimal Setup (Works out of the box)

```bash
# Server
PORT=8000

# Memory - Start with Supermemory (simplest)
MEMORY_BACKEND=supermemory
SUPERMEMORY_BASE_URL=https://api.supermemory.ai
SUPERMEMORY_API_KEY=  # Get free key at supermemory.ai

# Features
CACHE_ENABLED=true
PROFILE_ENABLED=true
```

### Alternative: Use Graphiti (More powerful, requires setup)

```bash
MEMORY_BACKEND=graphiti
MCP_SEARCH_ENDPOINT=http://localhost:5000/mcp/search
MCP_STORE_ENDPOINT=http://localhost:5000/mcp/store
```

**Note:** Graphiti requires Neo4j + MCP server. See `python-proxy/MCP_SETUP_GUIDE.md`

## Run

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Test

```bash
# Health check
curl http://localhost:8000/health

# Test chat (replace YOUR_OPENAI_KEY)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_OPENAI_KEY" \
  -H "X-User-Id: test-user" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Use with Msty Studio

1. Open Msty settings
2. Add Custom Provider:
   - **Name**: Memory Router
   - **Base URL**: `http://localhost:8000/v1`
   - **API Key**: Your actual LLM provider key (OpenAI, Anthropic, etc.)
3. Start chatting!

## Create Your Profile (Optional but Recommended)

```python
# In Python shell or script
from modules.profile_manager import get_profile_manager, UserProfile

manager = get_profile_manager()

profile = UserProfile(
    user_id="test-user",  # Match X-User-Id header
    name="Your Name",
    role="Your Role",
    goals=["Goal 1", "Goal 2"],
    studying=["Topic 1", "Topic 2"]
)

manager.create(profile)
```

## Verify Features

Check response headers:

```bash
curl -i http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "X-User-Id: test-user" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Test"}]}'
```

Look for:
```
X-Memory-Backend-Type: supermemory
X-Memory-Cache-Hit: false
X-Memory-Profile-Found: true
X-Memory-Context-Modified: true
```

## Troubleshooting

### Proxy won't start

**Error: `No module named 'fastapi'`**
```bash
pip install -r requirements.txt
```

**Error: `Port 8000 already in use`**
```bash
# Change port in .env
PORT=8001
```

### Memory not working

**Check backend:**
```bash
# If using Supermemory cloud
# Verify SUPERMEMORY_API_KEY is set

# If using Graphiti
curl http://localhost:5000/health
```

**Disable memory temporarily:**
```bash
# In .env
MEMORY_ENABLED=false
```

### No profile found

**Create profile (see above) or disable:**
```bash
# In .env
PROFILE_ENABLED=false
```

## Next Steps

- **Full Documentation**: `python-proxy/README.md`
- **Usage Guide**: `python-proxy/USAGE_GUIDE.md`
- **New Features**: `python-proxy/NEW_FEATURES.md`
- **MCP Setup**: `python-proxy/MCP_SETUP_GUIDE.md`
- **Comparison**: `COMPARISON.md`

## Quick Reference

| Feature | Config | Default |
|---------|--------|---------|
| Memory Backend | `MEMORY_BACKEND` | `graphiti` |
| Cache | `CACHE_ENABLED` | `true` |
| Profiles | `PROFILE_ENABLED` | `true` |
| Port | `PORT` | `8000` |

## Support

- Issues: Check troubleshooting section
- Documentation: See guides in `python-proxy/`
- Examples: `python-proxy/example_usage.py`

---

**You're ready to go! 🎉**

Memory Router Proxy is now running with:
- ✅ Automatic memory between chats
- ✅ 80-90% cache hit rate (super fast)
- ✅ Profile context (AI knows who you are)
- ✅ OpenAI-compatible API
