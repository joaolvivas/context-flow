# 🔄 Mac Reboot Guide - Memory System

**Use this guide after restarting your Mac to get everything running again.**

---

## Quick Start (1 Command)

```bash
cd "/Users/joaolucas/Desktop/Proxy Orchestrator/proxy-orchestrator" && ./start_memory_system.sh
```

That's it! The script will:
1. ✅ Start Redis
2. ✅ Start Graphiti HTTP Wrapper (port 5001)
3. ✅ Start Memory Proxy (port 8000)

---

## What Gets Started

| Service | Port | Purpose |
|---------|------|---------|
| **Redis** | 6379 | Tier 1 (working memory) + Tier 2 (session facts) |
| **Graphiti HTTP** | 5001 | Bridge to Neo4j AuraDB (Tier 3) |
| **Memory Proxy** | 8000 | Main proxy server |

---

## Verify Everything is Running

### Check Services
```bash
# Redis
redis-cli ping
# Should output: PONG

# Graphiti
curl http://localhost:5001/health
# Should return JSON

# Memory Proxy
curl http://localhost:8000/health
# Should return JSON with status: "ok"
```

### Check Processes
```bash
# See what's running on each port
lsof -i :6379  # Redis
lsof -i :5001  # Graphiti
lsof -i :8000  # Memory Proxy
```

---

## Monitor Logs

```bash
# Proxy activity (real-time)
tail -f /tmp/proxy_v3.log

# Graphiti processing (background)
tail -f /tmp/http_wrapper.log

# Redis health
redis-cli INFO
```

---

## Msty Configuration

**After services are running:**

1. Open Msty Settings
2. Configure API:
   - **Base URL**: `http://localhost:8000`
   - **API Key**: Your OpenAI API key (from .env file)
   - **Model**: Any OpenAI model (gpt-4o-mini, gpt-4o, etc)

3. Start chatting!
   - Your user_id is: `lucas-ai` (shared across all clients)
   - All your Neo4j memories are accessible

---

## Test Your Memory

```bash
# Quick test
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_OPENAI_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Qual é meu nome?"}]
  }'

# Should respond with your name from Neo4j memories
```

---

## Stop Services

```bash
# Stop Memory Proxy
lsof -ti:8000 | xargs kill

# Stop Graphiti
lsof -ti:5001 | xargs kill

# Stop Redis
brew services stop redis
```

---

## Troubleshooting

### Services Won't Start

**Redis issues:**
```bash
# Reinstall if needed
brew services stop redis
brew reinstall redis
brew services start redis
```

**Port already in use:**
```bash
# Kill whatever is using the port
lsof -ti:8000 | xargs kill -9
lsof -ti:5001 | xargs kill -9
```

**Python venv issues:**
```bash
cd python-proxy
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### No Memories Retrieved

1. **Check user_id in .env:**
   ```bash
   cat python-proxy/.env | grep DEFAULT_USER_ID
   # Should show: DEFAULT_USER_ID=lucas-ai
   ```

2. **Check Neo4j connection:**
   ```bash
   tail -f /tmp/http_wrapper.log | grep -i error
   ```

3. **Check if Graphiti is responding:**
   ```bash
   curl http://localhost:5001/health
   ```

### Context Not Being Injected

Check the logs for tier usage:
```bash
tail -f /tmp/proxy_v3.log | grep "Memory tiers used"
```

Should see:
- Simple queries: `['working_memory']`
- Factual queries: `['working_memory', 'session_facts', 'graphiti']`
- Deep queries: `['working_memory', 'session_facts', 'graphiti']`

---

## File Locations

| What | Where |
|------|-------|
| **Project** | `/Users/joaolucas/Desktop/Proxy Orchestrator/proxy-orchestrator` |
| **Main Code** | `python-proxy/` directory |
| **Graphiti** | `/Users/joaolucas/graphiti/mcp_server` |
| **Config** | `python-proxy/.env` |
| **Logs** | `/tmp/proxy_v3.log` and `/tmp/http_wrapper.log` |

---

## Git Repository

**Repository:** https://github.com/joaolvivas/context-flow
**Branch:** `claude/memory-orchestrator-proxy-011CUp8RL7ZqyhvNvJxcLmJ3`

**Pull latest changes:**
```bash
cd "/Users/joaolucas/Desktop/Proxy Orchestrator/proxy-orchestrator"
git pull origin claude/memory-orchestrator-proxy-011CUp8RL7ZqyhvNvJxcLmJ3
```

---

## System Architecture

```
┌─────────────┐
│    Msty     │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────┐
│   Memory Proxy (port 8000)      │
│   - Receives chat requests      │
│   - Injects memory context      │
│   - Routes to OpenAI            │
└────┬──────────────┬─────────────┘
     │              │
     ▼              ▼
┌────────────┐  ┌──────────────┐
│   Redis    │  │  Graphiti    │
│ (Tier 1+2) │  │  HTTP:5001   │
│  port:6379 │  │  (Tier 3)    │
└────────────┘  └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │  Neo4j Aura  │
                │  (Cloud DB)  │
                └──────────────┘
```

---

## Important Notes

1. **Always use the startup script** instead of starting services manually
2. **User ID is lucas-ai** - this gives you access to your Neo4j memories
3. **OpenAI API key required** - set in `python-proxy/.env`
4. **Logs are in /tmp** - they clear on reboot, which is fine
5. **Redis and Graphiti must be running** before starting the proxy

---

## Need Help?

Check these files:
- `QUICKSTART.md` - Usage examples
- `python-proxy/README.md` - Technical details
- `python-proxy/modules/memory/README.md` - 3-tier architecture docs

Or check the logs:
```bash
# See what went wrong
tail -100 /tmp/proxy_v3.log
tail -100 /tmp/http_wrapper.log
```

---

**Last Updated:** 2025-11-05 (Context injection fix applied)
