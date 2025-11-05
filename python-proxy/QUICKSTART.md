# 🚀 Quick Start - 3-Tier Memory System

## Services Running ✅

All systems are operational:
- ✅ **Redis**: localhost:6379
- ✅ **Graphiti HTTP Wrapper**: localhost:5001
- ✅ **Memory Proxy**: localhost:8000

---

## 🆕 New Features

- **Bilingual Support**: Works in both Portuguese and English
- **Tier 2 Fact Extraction**: Now fully operational (requires OpenAI API key)
- **Professional Query Detection**: Automatically uses Tier 3 for career/background queries

---

## Use with Msty Right Now

### 1. Configure Msty
Point Msty to your memory proxy:
- **API Endpoint**: `http://localhost:8000`
- **API Key**: Your OpenAI API key (REQUIRED - get it from https://platform.openai.com/api-keys)

### 2. Start Chatting

The system will automatically:
- Store recent turns in **Tier 1** (instant, free)
- Extract facts to **Tier 2** (fast, cheap)
- Queue complex memories to **Tier 3** (deep, as needed)

### 3. Try These Examples

**Store a fact (English or Portuguese):**
```
You: "My dog's name is Max and I love black color"
You: "Meu nome é João Lucas e sou media buyer"
```

**Ask a simple question (uses Tier 1+2, ~100ms):**
```
You: "What's my dog's name?"
You: "Qual é meu nome?"
→ Fast response from Redis cache!
```

**Ask about your background (uses all 3 tiers, ~1-2s):**
```
You: "Tell me about my professional background"
You: "Me conte sobre meu background profissional"
→ Comprehensive response from Neo4j knowledge graph!
```

**Ask a deep question (uses all 3 tiers, ~1-2s):**
```
You: "Remember everything we discussed earlier?"
You: "Me conte toda a informação que você tem sobre mim"
→ Comprehensive response from working memory + facts + knowledge graph
```

---

## Monitor Performance

### Watch Tier Usage
```bash
# See which tiers are used for each query
tail -f /tmp/proxy_v3.log | grep "Memory tiers used"
```

### Check Cost Savings
```bash
# View cost estimates
tail -f /tmp/proxy_v3.log | grep "Cost estimate"
```

### Background Processing
```bash
# Monitor Graphiti queue
tail -f /tmp/http_wrapper.log | grep "Completed add_episode"
```

---

## Run Test Suite

```bash
cd /Users/joaolucas/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
./test_3_tier_memory.sh
```

This will verify:
- ✅ All 3 tiers working
- ✅ Intelligent routing
- ✅ Performance targets met
- ✅ Cost savings achieved

---

## Expected Performance

### Simple Queries (90% of usage)
- **Response time**: 50-100ms
- **Token cost**: 100-300 tokens
- **Tiers used**: 1 + 2 (no Graphiti!)

### Complex Queries (10% of usage)
- **Response time**: 1-2 seconds
- **Token cost**: 600-800 tokens
- **Tiers used**: 1 + 2 + 3 (full power)

**Overall savings: 50-80% compared to Graphiti-only!**

---

## Restart Services (if needed)

```bash
# Start all services
brew services start redis
cd /Users/joaolucas/graphiti/mcp_server
HTTP_PORT=5001 uv run python http_wrapper.py &
cd /Users/joaolucas/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
source venv/bin/activate && python main.py &
```

Or use the startup script:
```bash
/Users/joaolucas/graphiti/mcp_server/start_with_proxy.sh
```

---

## View Detailed Documentation

- **Complete Migration Guide**: `MIGRATION_COMPLETE.md`
- **3-Tier Architecture**: `modules/memory/README.md`
- **Test Results**: Run `./test_3_tier_memory.sh`

---

## What to Expect in Msty

### First Message
```
You: "My favorite color is black"
Msty: "That's great! I'll remember that."

Behind the scenes:
→ Tier 1: Stored conversation turn (instant)
→ Tier 2: Extracting fact "favorite color = black" (~2s)
→ Tier 3: Queuing for graph storage (~15s background)
```

### Second Message (after 3 seconds)
```
You: "What's my favorite color?"
Msty: "Your favorite color is black."

Behind the scenes:
→ Tier 1: Recent conversation context (instant)
→ Tier 2: Retrieved fact from Redis (5ms)
→ Tier 3: NOT USED (Saved ~500 tokens!)
Response time: ~80ms ✅
```

### Deep Query
```
You: "Remember when we talked about colors?"
Msty: "Yes, you mentioned your favorite color is black..."

Behind the scenes:
→ Tier 1: Recent turns (instant)
→ Tier 2: Color facts (5ms)
→ Tier 3: Historical graph search (1s)
Response time: ~1.2s ✅
```

---

## Key Advantages

✅ **Instant conversation continuity** (Tier 1)  
✅ **Fast fact retrieval** (Tier 2)  
✅ **Deep knowledge** when needed (Tier 3)  
✅ **50-80% cost savings**  
✅ **No breaking changes** - everything just works!

---

## Need Help?

Check the logs:
```bash
# Proxy activity
tail -f /tmp/proxy_v3.log

# Graphiti processing
tail -f /tmp/http_wrapper.log

# Redis health
redis-cli INFO
```

**Your system is ready to use! Start chatting in Msty now! 🎉**
