# Usage Guide

> How to implement the Memory Router Proxy in your application

Add unlimited memory to your LLM applications with just a URL change. **100% free, self-hosted, and private.**

## Prerequisites

You'll need:

1. **Python 3.9+** installed
2. **Neo4j database** (for Graphiti memory storage)
3. **MCP/Graphiti server** running (optional but recommended)
4. Your **LLM provider's API key** (OpenAI, Anthropic, etc.)

## Quick Start

<Steps>
  <Step title="Clone and Install">
    ```bash
    git clone <your-repo>
    cd proxy-orchestrator

    # Create virtual environment
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt
    ```
  </Step>

  <Step title="Configure Environment">
    ```bash
    cp .env.example .env
    ```

    Edit `.env` with your settings:

    ```bash
    # Server
    HOST=0.0.0.0
    PORT=8000

    # Default LLM Provider
    DEFAULT_PROVIDER_URL=https://api.openai.com/v1
    DEFAULT_MODEL=gpt-4o-mini

    # MCP/Graphiti Endpoints (adjust if needed)
    MCP_SEARCH_ENDPOINT=http://localhost:5000/mcp/search
    MCP_STORE_ENDPOINT=http://localhost:5000/mcp/store

    # Memory Settings
    MEMORY_ENABLED=true
    MEMORY_SEARCH_LIMIT=5
    MEMORY_MAX_CONTEXT_TOKENS=2000
    MEMORY_CHUNK_SIZE=500
    ```
  </Step>

  <Step title="Start the Proxy">
    ```bash
    python main.py
    ```

    You should see:
    ```
    INFO:     Started server process
    INFO:     Uvicorn running on http://0.0.0.0:8000
    ```
  </Step>

  <Step title="Test the Connection">
    ```bash
    curl http://localhost:8000/health
    ```

    Should return:
    ```json
    {
      "status": "ok",
      "timestamp": "2024-01-15T10:30:00",
      "components": {"memory": true}
    }
    ```
  </Step>
</Steps>

## Base URL Configuration

Simply replace your provider's base URL with:

```
http://localhost:8000/v1
```

**That's it!** The proxy will automatically:
- Search for relevant memories
- Inject context into your prompts
- Store new memories asynchronously
- Forward requests to your LLM provider

## Provider Configuration

Your proxy can route to any OpenAI-compatible provider. Configure via:

1. **Default provider** (in `.env`):
   ```bash
   DEFAULT_PROVIDER_URL=https://api.openai.com/v1
   ```

2. **Per-request override** (via header):
   ```
   X-Provider-URL: https://api.anthropic.com/v1
   ```

### Supported Providers

<CodeGroup>
  ```text OpenAI
  https://api.openai.com/v1
  ```

  ```text Anthropic
  https://api.anthropic.com/v1
  ```

  ```text Groq
  https://api.groq.com/openai/v1
  ```

  ```text OpenRouter
  https://openrouter.ai/api/v1
  ```

  ```text DeepInfra
  https://api.deepinfra.com/v1/openai
  ```

  ```text Local (Ollama)
  http://localhost:11434/v1
  ```
</CodeGroup>

## Implementation Examples

<Tabs>
  <Tab title="Python">
    ```python
    from openai import OpenAI

    # Initialize client with Memory Router Proxy
    client = OpenAI(
        api_key="YOUR_OPENAI_API_KEY",  # Your actual LLM provider key
        base_url="http://localhost:8000/v1",  # Memory Router Proxy
        default_headers={
            "X-User-Id": "alice_123",  # Unique user identifier
            # Optional: Override default provider
            # "X-Provider-URL": "https://api.openai.com/v1"
        }
    )

    # Use as normal - memory is automatic!
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "My favorite color is blue"}
        ]
    )

    print(response.choices[0].message.content)

    # Later, in a new conversation...
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "What's my favorite color?"}
        ]
    )
    # Will remember "blue" from previous conversation!
    ```

    **With conversation tracking:**
    ```python
    import uuid

    # Generate conversation ID
    conversation_id = str(uuid.uuid4())

    # First message
    response1 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "My name is Alice"}],
        extra_body={"conversation_id": conversation_id}
    )

    # Continue same conversation
    response2 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What's my name?"}],
        extra_body={"conversation_id": conversation_id}
    )
    ```

    **Accessing diagnostic headers:**
    ```python
    from openai import OpenAI
    import httpx

    # Use httpx to access response headers
    with httpx.Client() as http_client:
        client = OpenAI(
            api_key="YOUR_KEY",
            base_url="http://localhost:8000/v1",
            http_client=http_client
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}]
        )

        # Check diagnostic headers
        headers = http_client.last_response.headers
        print(f"Chunks Retrieved: {headers.get('X-Memory-Chunks-Retrieved')}")
        print(f"Tokens Processed: {headers.get('X-Memory-Tokens-Processed')}")
        print(f"Memory Context: {headers.get('X-Memory-Tokens-Memory')}")
    ```
  </Tab>

  <Tab title="TypeScript">
    ```typescript
    import OpenAI from 'openai';

    // Initialize client with Memory Router Proxy
    const client = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,  // Your actual LLM provider key
      baseURL: 'http://localhost:8000/v1',  // Memory Router Proxy
      defaultHeaders: {
        'X-User-Id': 'alice_123'  // Unique user identifier
        // Optional: Override default provider
        // 'X-Provider-URL': 'https://api.openai.com/v1'
      }
    });

    // Use as normal - memory is automatic!
    const response = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'user', content: 'My favorite color is blue' }
      ]
    });

    console.log(response.choices[0].message.content);

    // Later, in a new conversation...
    const response2 = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'user', content: "What's my favorite color?" }
      ]
    });
    // Will remember "blue" from previous conversation!
    ```

    **With conversation tracking:**
    ```typescript
    import { v4 as uuidv4 } from 'uuid';

    // Generate conversation ID
    const conversationId = uuidv4();

    // First message
    const response1 = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: 'My name is Alice' }],
      conversation_id: conversationId  // Custom field
    });

    // Continue same conversation
    const response2 = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: "What's my name?" }],
      conversation_id: conversationId
    });
    ```

    **Accessing diagnostic headers:**
    ```typescript
    import axios from 'axios';

    const response = await axios.post(
      'http://localhost:8000/v1/chat/completions',
      {
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: 'Hello!' }]
      },
      {
        headers: {
          'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
          'X-User-Id': 'alice_123'
        }
      }
    );

    // Access diagnostic headers
    console.log('Chunks Retrieved:', response.headers['x-memory-chunks-retrieved']);
    console.log('Tokens Processed:', response.headers['x-memory-tokens-processed']);
    console.log('Memory Context:', response.headers['x-memory-tokens-memory']);
    ```
  </Tab>

  <Tab title="cURL">
    ```bash
    curl -X POST "http://localhost:8000/v1/chat/completions" \
      -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
      -H "X-User-Id: alice_123" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "gpt-4o-mini",
        "messages": [
          {"role": "user", "content": "My favorite color is blue"}
        ]
      }'
    ```

    **View diagnostic headers:**
    ```bash
    curl -i -X POST "http://localhost:8000/v1/chat/completions" \
      -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
      -H "X-User-Id: alice_123" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello!"}]
      }'

    # Look for X-Memory-* headers in response
    ```

    **With conversation tracking:**
    ```bash
    # Generate a conversation ID (use same ID for related messages)
    CONV_ID="conv_$(uuidgen)"

    # First message
    curl -X POST "http://localhost:8000/v1/chat/completions" \
      -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
      -H "X-User-Id: alice_123" \
      -H "Content-Type: application/json" \
      -d "{
        \"model\": \"gpt-4o-mini\",
        \"messages\": [{\"role\": \"user\", \"content\": \"My name is Alice\"}],
        \"conversation_id\": \"$CONV_ID\"
      }"

    # Continue conversation
    curl -X POST "http://localhost:8000/v1/chat/completions" \
      -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
      -H "X-User-Id: alice_123" \
      -H "Content-Type: application/json" \
      -d "{
        \"model\": \"gpt-4o-mini\",
        \"messages\": [{\"role\": \"user\", \"content\": \"What's my name?\"}],
        \"conversation_id\": \"$CONV_ID\"
      }"
    ```
  </Tab>

  <Tab title="Msty Studio">
    **Setup in Msty Studio:**

    1. Open Msty Studio settings
    2. Navigate to **Providers** → **Add Custom Provider**
    3. Configure:
       - **Name**: Memory Router
       - **Base URL**: `http://localhost:8000/v1`
       - **API Key**: Your actual LLM provider key (e.g., OpenAI key)
       - **Model**: `gpt-4o-mini` (or any model your provider supports)
    4. Save and select the provider

    **That's it!** All conversations through this provider now have automatic memory.

    **Optional: Set User ID**

    In Msty's custom headers (if supported):
    ```
    X-User-Id: your_unique_user_id
    ```
  </Tab>
</Tabs>

## Conversation Management

### Tracking Conversations

Use `conversation_id` to track multi-turn conversations:

```python
import uuid

# Start a new conversation
conversation_id = str(uuid.uuid4())

response1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "My project is about AI"}],
    extra_body={"conversation_id": conversation_id}
)

# Continue the same conversation (even days later)
response2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What was my project about?"}],
    extra_body={"conversation_id": conversation_id}
)
# Will remember "AI" from the first message
```

**Benefits:**
- Track conversation history
- Analyze conversation patterns
- Debug memory issues
- Group related interactions

### User Identification

Always provide a unique `X-User-Id` to isolate memories between users:

```python
# Alice's client - separate memory space
client_alice = OpenAI(
    api_key="YOUR_KEY",
    base_url="http://localhost:8000/v1",
    default_headers={"X-User-Id": "alice_123"}
)

# Bob's client - separate memory space
client_bob = OpenAI(
    api_key="YOUR_KEY",
    base_url="http://localhost:8000/v1",
    default_headers={"X-User-Id": "bob_456"}
)

# Alice's memories won't leak to Bob!
```

**If no User ID is provided:**
The proxy falls back to the client's IP address. This works for single-user setups but is NOT recommended for multi-user applications.

## Memory Control

### Disable Memory Per Request

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Temporary question"}],
    extra_body={"memory_enabled": False}  # No memory for this request
)
```

### Disable Memory Globally

In `.env`:
```bash
MEMORY_ENABLED=false
```

The proxy will work as a transparent pass-through without memory features.

## Response Headers

Every response includes diagnostic headers:

```http
X-Memory-Conversation-Id: 550e8400-e29b-41d4-a716-446655440000
X-Memory-Context-Modified: true
X-Memory-Chunks-Retrieved: 3
X-Memory-Chunks-Created: 2
X-Memory-Tokens-Input: 450
X-Memory-Tokens-Output: 320
X-Memory-Tokens-Memory: 180
X-Memory-Tokens-Processed: 950
X-Memory-Processing-Time-Ms: 145
X-Memory-Error: <if any error occurred>
```

**Use these to:**
- Monitor memory effectiveness
- Debug issues
- Track token usage
- Optimize chunk sizes

## Advanced Configuration

### Token Optimization

Control how many tokens are used for memory context:

```bash
# .env
MEMORY_MAX_CONTEXT_TOKENS=2000  # Max tokens for memories (default: 2000)
```

**Higher values:**
- ✅ More context
- ❌ Higher costs
- ❌ Slower responses

**Lower values:**
- ✅ Lower costs
- ✅ Faster responses
- ❌ Less context

### Chunking Configuration

Control how long messages are split:

```bash
# .env
MEMORY_CHUNK_SIZE=500  # Tokens per chunk (default: 500)
```

**Smaller chunks (200-300):**
- ✅ Better retrieval granularity
- ❌ More chunks to store

**Larger chunks (800-1000):**
- ✅ Fewer chunks
- ❌ Less precise retrieval

### Memory Search Limit

Control how many memories are retrieved:

```bash
# .env
MEMORY_SEARCH_LIMIT=5  # Max memories to search (default: 5)
```

## Troubleshooting

### Memory Not Working

**Check MCP endpoints:**
```bash
curl http://localhost:5000/mcp/search
```

If MCP is not running, the proxy will work as a pass-through (no memory).

**Check logs:**
```bash
python main.py
# Watch for "memory" related log entries
```

### Slow Responses

Memory search has a 1.5s timeout. If responses are slow:

1. **Check MCP performance**: Is Graphiti/Neo4j responding quickly?
2. **Reduce search limit**: Lower `MEMORY_SEARCH_LIMIT` in `.env`
3. **Reduce context tokens**: Lower `MEMORY_MAX_CONTEXT_TOKENS`

### Memory Not Relevant

If retrieved memories aren't relevant:

1. **Check chunk size**: Try different `MEMORY_CHUNK_SIZE` values
2. **Check Graphiti indexing**: Is Graphiti extracting entities correctly?
3. **Increase search limit**: Higher `MEMORY_SEARCH_LIMIT` = more candidates

## Production Deployment

### Recommended Setup

```bash
# Use production WSGI server
pip install gunicorn

# Run with multiple workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Security Considerations

1. **Use HTTPS in production** (reverse proxy with nginx/caddy)
2. **Set CORS_ORIGINS** to specific domains (not `*`)
3. **Rate limit** is enabled by default (60 req/min)
4. **Monitor logs** for suspicious activity

## Need Help?

- **Documentation**: See `README.md` for architecture details
- **Examples**: Check `example_usage.py` for code samples
- **Issues**: Report bugs in the repository

## Comparison to Cloud Solutions

| Feature | Cloud (Supermemory) | Self-Hosted (You) |
|---------|---------------------|-------------------|
| **Cost** | $20/month | **FREE** |
| **Privacy** | Data in cloud | **Your infrastructure** |
| **Customization** | Limited | **Full control** |
| **Memory Type** | Vector search | **Graph DB (superior)** |
| **Setup Time** | 5 minutes | 15-30 minutes |
| **Vendor Lock-in** | Yes | **No** |

**You get enterprise features for free!** 🎉
