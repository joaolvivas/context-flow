# MemoryStack Integration with Msty Studio

Msty Studio is a desktop AI chat application that works with multiple LLM providers. MemoryStack works perfectly with Msty to give your chats persistent memory.

## Setup (5 minutes)

### 1. Start MemoryStack

```bash
# Option A: Docker (Recommended)
cd memorystack
docker-compose up -d

# Option B: Manual
cd memorystack
./install.sh
python -m uvicorn src.memorystack.main:app --host 0.0.0.0 --port 8000
```

Verify it's running:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok",...}
```

### 2. Configure Msty

1. **Open Msty Studio**

2. **Add Custom Provider**:
   - Go to: Settings → Providers → Add Custom Provider
   - Name: `MemoryStack (OpenAI)`
   - Base URL: `http://localhost:8000`
   - API Key: Your actual OpenAI API key (e.g., `sk-proj-...`)
   - Save

3. **Select the Provider**:
   - In a new chat, select your "MemoryStack (OpenAI)" provider
   - Choose a model (e.g., `gpt-4o-mini`)

### 3. Test It

**First Chat:**
```
You: My name is João Lucas and I'm a media buyer
AI: Nice to meet you, João Lucas! As a media buyer...
```

**Open a NEW Chat (different conversation):**
```
You: What's my name and what do I do?
AI: Your name is João Lucas and you're a media buyer.
```

🎉 **It remembers!** Even in a completely new chat window.

---

## How It Works

```
Msty Studio → MemoryStack (localhost:8000) → OpenAI API
                    ↓
               Memory System
             (Redis + Neo4j/Graphiti)
```

1. **You chat in Msty** normally
2. **MemoryStack intercepts** the request
3. **Searches memory** for relevant context
4. **Injects context** automatically (you don't see this)
5. **Forwards to OpenAI** with enriched prompt
6. **Stores new info** in background

## Advanced Configuration

### Multiple Users

If multiple people use the same Msty instance:

```bash
# Edit .env
USER_ID_HEADER=X-User-Id

# Then in Msty, add custom header:
X-User-Id: joao
```

### Different Backends

**Use Supermemory instead of Graphiti:**
```bash
# Edit .env
MEMORY_BACKEND=supermemory
SUPERMEMORY_API_KEY=your-key
```

**Use custom backend:**
Implement your own adapter (see `src/memorystack/backends/base.py`)

### Memory Control

**Disable memory for specific chats:**
- Use a different provider in Msty without MemoryStack
- Or temporarily stop MemoryStack: `docker-compose stop`

**Clear memory:**
```bash
# Clear Redis (Tier 1 & 2)
redis-cli FLUSHALL

# Clear Neo4j (Tier 3) - be careful!
# This requires Cypher queries in Neo4j browser
```

---

## Troubleshooting

### ❌ Msty shows "Connection Error"

**Check MemoryStack is running:**
```bash
curl http://localhost:8000/health
```

**Check the Base URL in Msty:**
- Should be: `http://localhost:8000`
- NOT: `http://localhost:8000/v1` (Msty adds /v1 automatically)

### ❌ Memory not working

**Check logs:**
```bash
# Docker
docker logs memorystack-proxy

# Manual
cat /tmp/proxy_v3.log
```

**Check Redis:**
```bash
redis-cli ping
# Should return: PONG
```

**Check memory headers:**
Use cURL to see diagnostic headers:
```bash
curl -i -X POST http://localhost:8000/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"test"}]}' \
  | grep X-Memory-
```

### ❌ Slow responses

**Check which tiers are being used:**
Look for `X-Memory-Tiers-Used` header. Should be:
- `working_memory` for simple queries (fast)
- `working_memory,session_facts` for factual queries (fast)
- All three only for deep historical queries (slower)

**Optimize:**
```bash
# Reduce working memory turns
WORKING_MEMORY_TURNS=5  # Default: 10

# Disable Tier 3 if not needed
GRAPHITI_ENABLED=false
```

---

## Tips & Tricks

### 1. **Use Different Chats for Different Topics**

MemoryStack groups memories by `conversation_id`. Each new Msty chat gets a unique ID, so:
- **Work Chat**: Remembers work projects
- **Personal Chat**: Remembers personal info
- **Learning Chat**: Remembers what you're studying

### 2. **Name Your Chats**

Msty allows naming chats. Use descriptive names:
- "Project Alpha Discussion"
- "Learning Python Basics"
- "Customer Support Issues"

MemoryStack will associate memories with these conversations.

### 3. **Test Memory Persistence**

Periodically ask: "What do you know about me?" to verify memory is working.

### 4. **Monitor Token Usage**

MemoryStack adds diagnostic headers:
```
X-Memory-Cost-Estimate: 232
X-Memory-Processing-Time-Ms: 125
```

Track these to understand cost savings (should be ~77% reduction).

### 5. **Bilingual Support**

Works in Portuguese too!
```
Você: Meu nome é João e sou desenvolvedor
AI: Olá João! Prazer em conhecer um desenvolvedor...

[Novo chat]
Você: Qual é meu nome?
AI: Seu nome é João.
```

---

## Performance Expectations

With MemoryStack, your Msty chats should:

- ✅ **Remember info** across different chat windows
- ✅ **Respond quickly** (~80-200ms for most queries)
- ✅ **Use less tokens** (77% reduction on average)
- ✅ **Work offline** (except for LLM API calls)

---

## What You're Getting

| Without MemoryStack | With MemoryStack |
|---------------------|------------------|
| Start fresh each chat | Remembers everything |
| Re-explain context | Context already there |
| 1000+ tokens per query | ~232 tokens average |
| $15/month (100K queries) | $3/month (80% savings) |
| Forget after closing | Permanent memory |

---

## Next Steps

- **[Examples](../python/)** - Code examples for programmatic use
- **[API Reference](../../docs/usage-guide.md)** - Full API documentation
- **[Troubleshooting](../../docs/troubleshooting.md)** - Common issues

---

**Questions?** [Open an issue](https://github.com/joaolvivas/memorystack/issues)

Enjoy your memory-enhanced Msty experience! 🧠✨
