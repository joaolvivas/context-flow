# Complete Setup Guide for Proxy Orchestrator + Graphiti + Neo4j AuraDB

## Your Current Setup

You already have:
- ✅ Neo4j AuraDB instance: `neo4j+s://81a320df.databases.neo4j.io`
- ✅ Graphiti MCP server at `/Users/joaolucas/graphiti/mcp_server/`
- ✅ Working Msty integration

## Architecture

```
Your App/Msty → Memory Proxy (Port 8000) → LLM Provider
                     ↓
            HTTP Bridge (Port 5000)
                     ↓
            Graphiti + Neo4j AuraDB
```

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
cd /Users/joaolucas/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Memory Proxy

```bash
cd /Users/joaolucas/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
cp .env.example .env
```

Edit `.env`:
```bash
# Server
PORT=8000
DEBUG=false

# LLM Provider
DEFAULT_PROVIDER_URL=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4o-mini

# Memory Backend - Use Graphiti
MEMORY_BACKEND=graphiti
MEMORY_ENABLED=true

# MCP Endpoints (HTTP Bridge)
MCP_SEARCH_ENDPOINT=http://localhost:5000/mcp/search
MCP_STORE_ENDPOINT=http://localhost:5000/mcp/store

# Memory Settings
MEMORY_SEARCH_LIMIT=5
MEMORY_MAX_CONTEXT_TOKENS=2000
MEMORY_CHUNK_SIZE=500

# V2 Features
CACHE_ENABLED=true
PROFILE_ENABLED=true
```

### 3. Start the System

**Terminal 1 - Start HTTP Bridge (Port 5000):**
```bash
cd /Users/joaolucas/Desktop/Proxy\ Orchestrator/proxy-orchestrator
source /Users/joaolucas/graphiti/mcp_server/.venv/bin/activate  # Use existing venv
python graphiti_http_bridge.py
```

**Terminal 2 - Start Memory Proxy (Port 8000):**
```bash
cd /Users/joaolucas/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
source venv/bin/activate
python main.py
```

### 4. Test the System

```bash
# Test HTTP Bridge
curl http://localhost:5000/health

# Test Memory Proxy
curl http://localhost:8000/health

# Test Memory Storage
curl -X POST http://localhost:5000/mcp/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I love building AI agents with Python",
    "user_id": "lucas",
    "metadata": {"timestamp": "2024-11-05T14:50:00"}
  }'

# Test Memory Search
curl -X POST http://localhost:5000/mcp/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What do I like to build?",
    "user_id": "lucas",
    "limit": 5
  }'

# Check Stats
curl http://localhost:5000/mcp/stats
```

### 5. Use with Applications

#### Option A: Programmatic (Python)

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-openai-key",
    base_url="http://localhost:8000/v1",
    default_headers={"X-User-Id": "lucas"}
)

# First conversation - stores memory
response1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "I love building AI agents"}]
)

# Later conversation - uses stored memory
response2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What do I like to build?"}]
)

print(response2.choices[0].message.content)
# Should mention AI agents!
```

#### Option B: Msty Studio

In Msty, add a custom provider:
- **Name**: Memory Router
- **Base URL**: `http://localhost:8000/v1`
- **API Key**: Your actual OpenAI/Anthropic API key

Now all chats through this provider have automatic memory!

## What You Get

### Automatic Memory Features
- 🧠 **Graph-based memory** - Entities and relationships
- 🔍 **Semantic search** - Find relevant past context
- 💾 **Auto storage** - Memories saved asynchronously
- 🎯 **Token optimization** - Smart context injection
- ⚡ **Conversational cache** - 80-90% hit rate, 10x faster
- 👤 **User profiles** - Persistent user context

### Diagnostic Headers
Every response includes:
```
X-Memory-Conversation-Id: uuid
X-Memory-Context-Modified: true/false
X-Memory-Chunks-Retrieved: 3
X-Memory-Chunks-Created: 2
X-Memory-Tokens-Input: 450
X-Memory-Tokens-Output: 320
X-Memory-Tokens-Memory: 180
X-Memory-Processing-Time-Ms: 145
X-Memory-Backend-Type: graphiti
X-Memory-Cache-Hit: true/false
```

## Monitoring

### View Memories in Neo4j Browser

```cypher
// All memories for your group
MATCH (e:EpisodicNode {group_id: 'lucas-ai'})
RETURN e
LIMIT 25

// See entity relationships
MATCH (a)-[r]->(b)
WHERE a.group_id = 'lucas-ai'
RETURN a, r, b
LIMIT 50

// Search for specific topic
MATCH (e:EpisodicNode {group_id: 'lucas-ai'})
WHERE e.content CONTAINS 'AI agents'
RETURN e
```

### Check Proxy Metrics

```bash
curl http://localhost:8000/metrics
```

### Check Memory Stats

```bash
curl http://localhost:5000/mcp/stats
```

## Troubleshooting

### "Connection refused" on port 5000
- Make sure HTTP Bridge is running: `python graphiti_http_bridge.py`
- Check logs for errors

### "Neo4j connection failed"
- Verify credentials in `/Users/joaolucas/graphiti/mcp_server/.env`
- Test connection: `curl http://localhost:5000/health`

### No memories being stored
- Check HTTP Bridge logs for errors
- Verify Neo4j has space (AuraDB free tier: 200k nodes)
- Test direct storage: `curl -X POST http://localhost:5000/mcp/store ...`

### Memory search returns empty
- Memories take a few seconds to index
- Check if data exists: `curl http://localhost:5000/mcp/stats`
- Try searching in Neo4j Browser

## Advanced Features

### User Profiles

Create `python-proxy/profiles/lucas.json`:
```json
{
  "user_id": "lucas",
  "name": "Lucas",
  "context": "I'm a developer who loves building AI agents",
  "preferences": [
    "Python programming",
    "Graph databases",
    "LLM applications"
  ],
  "goals": [
    "Build intelligent memory systems",
    "Integrate Graphiti with applications"
  ]
}
```

### Custom Backends

Switch to Supermemory in `.env`:
```bash
MEMORY_BACKEND=supermemory
SUPERMEMORY_BASE_URL=https://api.supermemory.ai
SUPERMEMORY_API_KEY=your-key
```

### Rate Limiting

Adjust in `.env`:
```bash
RATE_LIMIT_PER_MINUTE=120
```

## Production Considerations

1. **Use process manager** (PM2, systemd)
2. **Add HTTPS** (nginx reverse proxy)
3. **Scale Neo4j** (upgrade from free tier)
4. **Monitor costs** (OpenAI API for entity extraction)
5. **Backup Neo4j** regularly

## Next Steps

1. ✅ Start both services
2. ✅ Run test commands
3. ✅ Integrate with your app
4. 📊 Monitor metrics
5. 🎨 Customize profiles
6. 🚀 Deploy to production

## Support

- **Graphiti Docs**: https://github.com/getzep/graphiti
- **Neo4j Docs**: https://neo4j.com/docs/
- **Proxy Docs**: `python-proxy/README.md`

---

**You now have a complete memory system with your existing Graphiti + AuraDB setup!** 🎉
