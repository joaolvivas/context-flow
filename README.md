# 🧠 Memory Orchestrator Proxy

An intelligent proxy server that enriches LLM requests with contextual memory from your personal knowledge graph via Graphiti MCP and Neo4j.

## 🎯 What It Does

This proxy sits between your LLM client (like Msty) and OpenAI, automatically:

1. **Intercepts** chat requests from your client
2. **Searches** your knowledge graph for relevant context (entities, facts, relationships)
3. **Enriches** the prompt with top-ranked memories
4. **Forwards** the enhanced request to OpenAI
5. **Streams** the response back to your client

**Result:** Your LLM conversations are now context-aware, pulling from your personal knowledge base automatically.

## ✨ Features (MVP v1.0)

- ✅ OpenAI API-compatible endpoint (`/v1/chat/completions`)
- ✅ Graphiti MCP integration via stdio transport
- ✅ Smart memory search (nodes + facts)
- ✅ Automatic context injection into system prompts
- ✅ **Streaming response support** (Server-Sent Events)
- ✅ Graceful degradation (works even if memory fails)
- ✅ Structured JSON logging
- ✅ Health check endpoint
- ✅ Environment-based configuration

## 🏗️ Architecture

```
Msty (or any OpenAI client)
        ↓
[Memory Orchestrator Proxy] :3000
        ↓
        ├─→ Graphiti MCP (stdio)
        │   ├─→ search_nodes(query, limit)
        │   ├─→ search_facts(query, limit)
        │   └─→ Neo4j Knowledge Graph
        ↓
OpenAI API (gpt-4-turbo / gpt-4o)
        ↓
Response → Back to Client
```

## 📦 Prerequisites

Before running this proxy, ensure you have:

1. **Node.js** >= 18.x installed
2. **Graphiti MCP server** installed (`@getzep/mcp-server-graphiti`)
3. **Neo4j** database running locally (via Graphiti)
4. **OpenAI API key** with access to GPT-4

### Verify Graphiti Installation

```bash
# Test that Graphiti MCP is accessible
npx @getzep/mcp-server-graphiti --help
```

If this fails, install Graphiti first:
```bash
npm install -g @getzep/mcp-server-graphiti
```

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd proxy-orchestrator
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
# Required
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Optional (defaults shown)
OPENAI_MODEL=gpt-4-turbo-preview
GRAPHITI_MCP_COMMAND=npx @getzep/mcp-server-graphiti
PROXY_PORT=3000
LOG_LEVEL=info
MEMORY_SEARCH_LIMIT=5
MEMORY_ENABLED=true
```

**Note:** If your Graphiti MCP requires Neo4j credentials, add them to your environment or Graphiti's config file.

### 3. Run the Proxy

```bash
# Development mode (auto-reload)
npm run dev

# Production mode
npm start
```

You should see:

```
🚀 Memory Orchestrator Proxy running on http://localhost:3000
📋 Available endpoints:
  GET  /health
  POST /v1/chat/completions (OpenAI compatible)
```

### 4. Test the Health Endpoint

```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "memory-orchestrator-proxy",
  "version": "1.0.0",
  "memory": {
    "enabled": true,
    "searchLimit": 5
  }
}
```

## 🔧 Configure Msty (or Your LLM Client)

### Msty Configuration

1. Open Msty settings
2. Navigate to **LLM Provider** settings
3. Add a **Custom OpenAI Provider**:
   - **Base URL:** `http://localhost:3000/v1`
   - **API Key:** Your actual OpenAI API key (proxy will forward it)
   - **Model:** `gpt-4-turbo-preview` (or your preferred model)

4. Save and test with a message

### Testing with curl

```bash
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4-turbo-preview",
    "messages": [
      {"role": "user", "content": "What companies have I applied to recently?"}
    ],
    "stream": false
  }'
```

**With streaming:**

```bash
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4-turbo-preview",
    "messages": [
      {"role": "user", "content": "Tell me about my TikTok campaigns"}
    ],
    "stream": true
  }'
```

## 🧪 How Memory Enrichment Works

### Example Flow

**User Query:** "What's my ROAS for TikTok campaigns?"

**Behind the Scenes:**

1. Proxy receives request from Msty
2. Extracts query: `"What's my ROAS for TikTok campaigns?"`
3. Searches Graphiti:
   - `search_nodes("TikTok ROAS campaigns")` → finds entities
   - `search_facts("TikTok ROAS campaigns")` → finds facts
4. Top 5 results ranked by relevance:
   ```
   - "Managed TikTok campaigns at $15K/day achieving 3.2 ROAS"
   - "Q4 2024: scaled to 700K monthly revenue"
   - "TikTok conversion rate improved to 4.8%"
   ```
5. Injects into system prompt:
   ```
   You are a helpful AI assistant with access to the user's personal knowledge graph.

   ---
   Relevant memories from your knowledge graph:

   1. TikTok Campaign Performance (relevance: 0.95)
      Managed TikTok campaigns at $15K/day achieving 3.2 ROAS

   2. Revenue Milestone (relevance: 0.87)
      Q4 2024: scaled to 700K monthly revenue
   ---
   ```
6. Sends enriched request to OpenAI
7. Streams response back to Msty

**User sees:** A context-aware answer referencing their actual campaign data!

## 📊 Logging

Logs are output to console in structured format:

```
2025-11-05 12:34:56 [info] 🚀 Memory Orchestrator Proxy running on http://localhost:3000
2025-11-05 12:35:02 [info] Received chat completion request
  {
    "messageCount": 1,
    "stream": true,
    "model": "gpt-4-turbo-preview"
  }
2025-11-05 12:35:03 [info] Found 3 relevant memories
  {
    "nodes": 2,
    "facts": 1
  }
2025-11-05 12:35:05 [info] Streaming response completed
  {
    "totalTime": 2847,
    "memoriesUsed": 3
  }
```

Adjust log verbosity via `LOG_LEVEL` env var: `error | warn | info | debug`

## 🛠️ Troubleshooting

### Proxy won't start

**Error:** `OPENAI_API_KEY is required`
- **Solution:** Check your `.env` file exists and has the API key

**Error:** `Cannot find module @modelcontextprotocol/sdk`
- **Solution:** Run `npm install`

### Memory enrichment not working

**Check logs for:**
```
Failed to connect to Graphiti MCP server
```

**Solutions:**
1. Verify Graphiti is installed: `npx @getzep/mcp-server-graphiti --help`
2. Check Neo4j is running: `neo4j status` (if applicable)
3. Try running Graphiti manually to see error messages
4. Set `MEMORY_ENABLED=false` to disable memory and use plain OpenAI

### Msty can't connect

**Error:** Connection refused
- **Solution:** Ensure proxy is running on `localhost:3000`
- Check firewall isn't blocking the port

**Error:** Authentication failed
- **Solution:** Verify you're passing your real OpenAI API key to Msty, not a dummy key

### No memories returned (even though Neo4j has data)

**Check:**
1. Does your query match data in Neo4j? Try a broader search
2. Is `MEMORY_SEARCH_LIMIT` too low? Increase it in `.env`
3. Check logs for "Found X relevant memories" - if 0, your graph might be empty for that topic

## 🔮 Roadmap

### V2 (Coming Soon)
- ✅ Memory persistence (`add_episode` after each conversation)
- ✅ Advanced relevance ranking algorithms
- ✅ Namespace support (separate contexts for job_search, ai_learning, marketing)
- ✅ Rate limiting and retry logic for OpenAI
- ✅ Metrics endpoint (`/metrics`)

### V3 (Future)
- ✅ Multi-MCP orchestration (Graphiti + other MCP servers)
- ✅ Web UI for knowledge graph visualization
- ✅ Analytics dashboard (costs, token usage, query patterns)
- ✅ Obsidian export for memories
- ✅ Memory decay/cleanup (forget old irrelevant data)

## 🤝 Contributing

This is a personal project built for a specific workflow, but contributions are welcome!

## 📄 License

MIT

## 💡 Use Cases

### Job Search Assistant
```
User: "Which companies should I follow up with?"
Proxy: [Searches: application_status, response_times, company_notes]
Response: Context-aware follow-up recommendations
```

### Learning Path
```
User: "What should I study next about MCP?"
Proxy: [Searches: topics_studied, knowledge_gaps, interests]
Response: Personalized learning suggestions
```

### Campaign Analysis
```
User: "How does my TikTok ROAS trend?"
Proxy: [Searches: campaign_metrics, roas_history, budget_changes]
Response: Historical analysis with your actual data
```

## 🙏 Acknowledgments

- [Graphiti](https://github.com/getzep/graphiti) - Knowledge graph memory layer
- [Model Context Protocol](https://modelcontextprotocol.io) - Standardized LLM-tool communication
- [OpenAI](https://openai.com) - LLM API

---

**Built with ❤️ for personal AI that actually remembers you**
