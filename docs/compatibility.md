# ⚡ ContextFlow Compatibility Guide

> **Simple rule:** If your tool lets you customize the API endpoint, ContextFlow works with it.

---

## Table of Contents

- [Quick Compatibility Check](#quick-compatibility-check)
- [Confirmed Compatible Tools](#confirmed-compatible-tools)
- [Known Incompatible Tools](#known-incompatible-tools)
- [How to Test Compatibility](#how-to-test-compatibility)
- [Compatibility Matrix](#compatibility-matrix)
- [Request Testing for Your Tool](#request-testing-for-your-tool)

---

## Quick Compatibility Check

### ✅ Your Tool is Compatible If:

Look for **any** of these settings in your tool:

#### In Settings/Preferences
- "Custom API endpoint"
- "Base URL"
- "API URL"
- "OpenAI API base"
- "OpenAI endpoint"
- "Custom endpoint"
- "Server URL"
- "LLM endpoint"

#### In Configuration Files
```yaml
# Example patterns
api_base: http://localhost:8000/v1
base_url: http://localhost:8000/v1
openai_api_base: http://localhost:8000/v1
endpoint: http://localhost:8000/v1
```

#### Via Environment Variables
```bash
OPENAI_API_BASE=http://localhost:8000/v1
ANTHROPIC_BASE_URL=http://localhost:8000/v1
LLM_BASE_URL=http://localhost:8000/v1
API_BASE_URL=http://localhost:8000/v1
```

#### Via Command-Line Flags
```bash
--api-base http://localhost:8000/v1
--base-url http://localhost:8000/v1
--openai-api-base http://localhost:8000/v1
--endpoint http://localhost:8000/v1
```

**If you find ANY of these → ContextFlow works! ⚡**

---

## Confirmed Compatible Tools

### 🎨 IDEs & Code Editors

| Tool | Status | Setup Difficulty | Notes |
|------|--------|------------------|-------|
| **Cursor** | ✅ Battle-tested | Easy | Settings → Models → Custom base URL |
| **VS Code + Continue** | ✅ Verified | Easy | Continue extension settings |
| **VS Code + Cody** | ✅ Verified | Easy | Cody extension settings |
| **Windsurf** | ✅ Verified | Easy | Settings → AI → Custom endpoint |
| **JetBrains AI** | ✅ Community | Medium | Requires plugin configuration |
| **Neovim + copilot.lua** | ✅ Community | Medium | Lua configuration |

**Setup time:** 2-5 minutes

**[See Cursor setup guide →](../examples/integrations/cursor_setup.md)**

**[See VS Code setup guide →](../examples/integrations/vscode_setup.md)**

---

### 🖥️ CLI AI Tools

| Tool | Status | Setup Difficulty | Command Flag |
|------|--------|------------------|--------------|
| **Aider** | ✅ Battle-tested | Easy | `--openai-api-base` |
| **Claude Code** | ✅ Verified | Easy | `ANTHROPIC_BASE_URL` env var |
| **Codex CLI** | ✅ Verified | Easy | `--api-base` |
| **Shell-GPT (sgpt)** | ✅ Community | Easy | `--api-base` |
| **Codeium CLI** | ✅ Community | Easy | Config file |
| **GitHub Copilot CLI** | ❌ | N/A | No custom endpoint support |

**Setup time:** 30 seconds (one command/env var)

**Example (Aider):**
```bash
aider --openai-api-base http://localhost:8000/v1
```

**Example (Claude Code):**
```bash
export ANTHROPIC_BASE_URL=http://localhost:8000/v1
claude-code
```

**Example (Shell-GPT):**
```bash
sgpt --api-base http://localhost:8000/v1 "your prompt"
```

---

### 💬 Chat Applications

| Tool | Status | Setup Difficulty | Notes |
|------|--------|------------------|-------|
| **Msty Studio** | ✅ Battle-tested | Easy | Add custom provider in settings |
| **Open WebUI** | ✅ Verified | Easy | Settings → Connections → OpenAI |
| **LibreChat** | ✅ Community | Easy | `.env` configuration |
| **BetterChatGPT** | ✅ Community | Easy | Settings → API Endpoint |
| **ChatGPT-Next-Web** | ✅ Community | Easy | Environment variable |
| **ChatGPT Web** | ❌ | N/A | Official site - no custom endpoint |
| **Claude.ai Web** | ❌ | N/A | Official site - no custom endpoint |

**Setup time:** 2-5 minutes

**[See Msty setup guide →](../examples/integrations/msty_setup.md)**

---

### 🐍 SDKs & Libraries

| SDK | Status | Setup | Example |
|-----|--------|-------|---------|
| **Python OpenAI** | ✅ Official | 1 line | `base_url="http://localhost:8000/v1"` |
| **Node.js OpenAI** | ✅ Official | 1 line | `baseURL: "http://localhost:8000/v1"` |
| **Go OpenAI** | ✅ Community | 1 line | Config option |
| **Ruby OpenAI** | ✅ Community | 1 line | Config option |
| **Rust OpenAI** | ✅ Community | 1 line | Builder pattern |
| **LangChain (Python)** | ✅ Verified | 1 line | `openai_api_base` param |
| **LangChain (JS/TS)** | ✅ Verified | 1 line | Configuration object |
| **LlamaIndex** | ✅ Verified | 1 line | `api_base` param |

**Setup time:** Literally one line of code

**Python Example:**
```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-...",
    base_url="http://localhost:8000/v1"  # 👈 Add this line
)
```

**Node.js Example:**
```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  apiKey: 'sk-...',
  baseURL: 'http://localhost:8000/v1'  // 👈 Add this line
});
```

**LangChain Python Example:**
```python
from langchain.llms import OpenAI

llm = OpenAI(
    openai_api_key="sk-...",
    openai_api_base="http://localhost:8000/v1"  # 👈 Add this
)
```

---

### 🤖 Autonomous Agents & Frameworks

| Framework | Status | Setup Difficulty | Notes |
|-----------|--------|------------------|-------|
| **AutoGPT** | ✅ Community | Easy | `.env` configuration |
| **BabyAGI** | ✅ Community | Easy | Environment variable |
| **LangGraph** | ✅ Verified | Easy | Same as LangChain |
| **CrewAI** | ✅ Community | Easy | Config file |
| **Semantic Kernel** | ✅ Community | Medium | Endpoint configuration |

---

## Known Incompatible Tools

### ❌ Cannot Work With:

| Tool/Platform | Reason | Alternative |
|---------------|--------|-------------|
| **ChatGPT Web (chatgpt.com)** | Hardcoded OpenAI endpoint | Use Cursor, Msty, or OpenAI SDK |
| **Claude.ai Web (claude.ai)** | Hardcoded Anthropic endpoint | Use Cursor, Claude Code CLI |
| **GitHub Copilot (official)** | Proprietary API, no custom endpoint | Use Cursor or Continue |
| **Official mobile apps** | Hardcoded endpoints | Use web alternatives with custom endpoints |
| **Proprietary enterprise tools** | Closed systems | Contact vendor for custom endpoint support |

### Why These Don't Work:

**Technical reason:** These tools make API requests directly to hardcoded URLs (e.g., `https://api.openai.com`) without allowing users to override the endpoint.

**They're not configurable** - there's no setting, environment variable, or configuration file that lets you change where requests go.

---

## How to Test Compatibility

### Step 1: Find the Endpoint Setting

1. **Check Settings/Preferences**
   - Look for "API", "endpoint", "base URL", or "OpenAI" in settings
   - Common locations:
     - Settings → Models
     - Preferences → AI/LLM
     - Configuration → API

2. **Check Configuration Files**
   - Look for `.env`, `config.yaml`, `settings.json`
   - Search for: `api`, `endpoint`, `base_url`, `url`

3. **Check Environment Variables**
   - Look in documentation for supported env vars
   - Common ones: `OPENAI_API_BASE`, `API_BASE_URL`, `LLM_ENDPOINT`

4. **Check Command-Line Flags**
   - Run `your-tool --help | grep -i "api\|endpoint\|base"`
   - Common flags: `--api-base`, `--base-url`, `--endpoint`

### Step 2: Test ContextFlow

1. **Start ContextFlow**
   ```bash
   docker-compose up -d
   # or
   python -m uvicorn src.contextflow.main:app --host 0.0.0.0 --port 8000
   ```

2. **Verify it's running**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "ok", ...}
   ```

3. **Configure your tool**
   - Set endpoint to: `http://localhost:8000/v1`
   - Keep your real API key (OpenAI, Anthropic, etc.)

4. **Send a test query**
   - Try a simple prompt: "Hello, can you hear me?"
   - Should respond normally

5. **Check the headers** (if accessible)
   - Look for `X-Memory-*` headers
   - Indicates ContextFlow is working

6. **Test memory**
   - First query: "My name is Alex and I love TypeScript"
   - Second query (new chat): "What's my name and what do I love?"
   - Should remember: "Alex" and "TypeScript"

### Step 3: Verify Success

✅ **It works if:**
- Queries get responses normally
- Second query remembers first query's information
- You see `X-Memory-*` headers (if you can inspect them)

❌ **It doesn't work if:**
- Connection refused errors
- "Invalid API endpoint" errors
- Tool ignores your endpoint setting
- No memory between conversations (but responses work)
  - This might mean your endpoint is set but tool isn't using it

---

## Compatibility Matrix

### By Category

| Category | Compatible Tools | Incompatible Tools | Success Rate |
|----------|-----------------|-------------------|--------------|
| **IDEs** | Cursor, VS Code (w/ extensions), Windsurf, JetBrains | - | 100% |
| **CLI Tools** | Aider, Claude Code, sgpt, custom scripts | GitHub Copilot CLI | 90% |
| **Chat Apps** | Msty, Open WebUI, LibreChat, self-hosted | ChatGPT.com, Claude.ai | 80% |
| **SDKs** | Python, Node.js, Go, Ruby, Rust | - | 100% |
| **Frameworks** | LangChain, LlamaIndex, AutoGPT | - | 100% |
| **Mobile** | - | All official apps | 0% |

### By Setup Difficulty

| Difficulty | Tools | Time | Technical Skill |
|------------|-------|------|-----------------|
| **Easy** | SDKs, most CLI tools, Cursor | 30 sec - 2 min | None |
| **Medium** | JetBrains, Neovim, some frameworks | 5-10 min | Basic config editing |
| **Hard** | Custom integrations, enterprise tools | 30+ min | Development required |

---

## Request Testing for Your Tool

Don't see your tool listed? We'll help you test it!

### Before Requesting

1. **Check if your tool supports custom endpoints**
   - Search documentation for "custom endpoint", "base URL", or "API URL"
   - Check settings/preferences
   - Look for environment variables

2. **Try testing it yourself** (see [How to Test](#how-to-test-compatibility))
   - It's quick and you'll learn in the process!

### Submit a Compatibility Request

**[Open an issue on GitHub](https://github.com/joaolvivas/contextflow/issues/new?template=compatibility_request.md)**

**Include:**
- Tool name and version
- Platform (Windows/Mac/Linux)
- Any endpoint settings you found
- Whether you tested it (and results)
- Screenshots of settings (if relevant)

**We'll:**
- Test compatibility within 48 hours
- Add it to this guide
- Create a setup guide if it works
- Suggest alternatives if it doesn't

---

## Common Compatibility Questions

### "My tool uses Anthropic's API, not OpenAI's. Will it work?"

**Maybe.** Check if your tool uses:
- **OpenAI-compatible format** - Yes, works! ✅
- **Native Anthropic SDK** - Depends on custom endpoint support

ContextFlow uses OpenAI's API format internally. If your tool expects Anthropic's native format, it may not work without a compatibility layer.

**Known to work:**
- Tools using OpenAI SDK with Anthropic models (via compatibility mode)
- Claude Code CLI (supports custom base URL)

**May not work:**
- Tools using Anthropic SDK directly without endpoint customization

### "Can I use this with local models (Ollama, LM Studio)?"

**Yes!** With an intermediate step:

```
Your Tool → ContextFlow → Ollama/LM Studio (with OpenAI compatibility)
```

**Requirements:**
- Your local model server must support OpenAI-compatible API
- Most do: Ollama, LM Studio, vLLM, Text Generation WebUI

**Setup:**
```bash
# 1. Start your local model with OpenAI compatibility
ollama serve  # Usually on localhost:11434

# 2. Point ContextFlow to it (in .env)
DEFAULT_PROVIDER_URL=http://localhost:11434/v1

# 3. Point your tool to ContextFlow
base_url=http://localhost:8000/v1
```

### "Does this work with Azure OpenAI?"

**Yes!** ContextFlow is a transparent proxy.

**Setup:**
```bash
# In .env
DEFAULT_PROVIDER_URL=https://your-resource.openai.azure.com
# Add Azure-specific headers if needed
```

Your tool still points to ContextFlow, ContextFlow forwards to Azure.

### "Can I use this with multiple tools at once?"

**Yes!** All tools sharing the same `X-User-Id` will share memory.

**Example:**
- Cursor IDE with `X-User-Id: alice`
- Python script with `X-User-Id: alice`
- CLI tool with `X-User-Id: alice`

**Result:** All three tools share the same memory pool. What you tell Cursor, your Python script knows!

**Pro tip:** Use different user IDs for different projects:
- `X-User-Id: alice-project-a`
- `X-User-Id: alice-project-b`

---

## Compatibility Roadmap

### Currently Supported ✅
- OpenAI-compatible APIs (standardized)
- Tools with custom endpoint configuration
- SDKs with base URL overrides

### Coming Soon 🚧
- Anthropic native format support (direct Claude API format)
- Gemini API compatibility layer
- GraphQL endpoint support
- gRPC endpoint support

### Community Contributions Welcome! 🤝
- Test your favorite tool
- Submit compatibility reports
- Create setup guides
- Help others in discussions

---

## Troubleshooting Compatibility

### Problem: "Connection refused" when testing

**Causes:**
- ContextFlow isn't running
- Wrong port (should be 8000)
- Firewall blocking localhost

**Solutions:**
```bash
# Check if running
curl http://localhost:8000/health

# Restart
docker-compose restart

# Check logs
docker-compose logs contextflow
```

### Problem: "Tool responds but doesn't remember"

**Causes:**
- Tool isn't using your custom endpoint (ignoring the setting)
- No `X-User-Id` header being sent
- Memory backend not configured

**Solutions:**
1. **Verify tool is using ContextFlow:**
   ```bash
   # Monitor requests
   docker-compose logs -f contextflow | grep "POST /v1/chat"
   ```
   - If you don't see requests when using tool → tool isn't using your endpoint

2. **Check if X-User-Id is required:**
   - Some integrations need explicit user ID
   - Add via headers or query params

3. **Check memory backend:**
   ```bash
   curl http://localhost:8000/health
   # Look for memory_backend status
   ```

### Problem: "Invalid API key" errors

**Cause:** Tool expects you to use a ContextFlow-specific API key

**Solution:** Use your **real** API key (OpenAI, Anthropic, etc.)
- ContextFlow is a proxy, not a replacement
- Your key goes through ContextFlow to the real provider

---

## Contributing Compatibility Info

Help the community by sharing your experiences!

### Found a Compatible Tool?

1. Test it thoroughly
2. Document the setup steps
3. Submit a PR adding it to this guide
4. Optionally: Create a detailed setup guide in `examples/integrations/`

### Found an Incompatible Tool?

1. Confirm it has no custom endpoint option
2. Note why it doesn't work
3. Suggest alternatives that do work
4. Add it to the "Known Incompatible" section

**[See contribution guidelines →](../CONTRIBUTING.md)**

---

## Updates to This Guide

This compatibility guide is living documentation. Tools change, new tools emerge, and we discover new compatibility information.

**Last updated:** 2024-11-05

**Recent additions:**
- Claude Code CLI (verified compatible)
- Shell-GPT / sgpt (community verified)
- JetBrains AI (community verified)
- LibreChat (community verified)

**Want to help keep this updated?**
- Test new tools
- Report compatibility changes
- Submit corrections

---

## Summary

**✅ Works with:**
- Any IDE with custom endpoint settings (Cursor, VS Code, etc.)
- Any CLI tool with `--base-url` or env var support (Aider, Claude Code, etc.)
- Any self-hosted chat app with endpoint configuration (Msty, Open WebUI, etc.)
- Any OpenAI-compatible SDK (Python, Node.js, Go, etc.)
- Any framework/agent system with endpoint override (LangChain, AutoGPT, etc.)

**❌ Doesn't work with:**
- Official closed web apps (ChatGPT.com, Claude.ai)
- Tools without custom endpoint configuration
- Tools with hardcoded API URLs
- Most official mobile apps

**🎯 Simple test:** Can you change the API endpoint in your tool's settings? If yes, ContextFlow works!

---

**Questions?** [Open a discussion →](https://github.com/joaolvivas/contextflow/discussions/new?category=compatibility)

**Found a bug in this guide?** [Report it →](https://github.com/joaolvivas/contextflow/issues/new)
