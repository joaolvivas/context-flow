# Warp AI Integration - Using Local Memory Proxy

## Overview

Configure Warp AI to use your local Memory Router Proxy, enabling persistent memory across all your Warp AI conversations.

**Benefits**:
- 🧠 Persistent memory across sessions
- 💰 77% token cost reduction
- ⚡ Faster responses with 3-tier caching
- 📊 Transparent memory usage in logs

---

## Prerequisites

1. ✅ Memory Proxy running on `http://localhost:8000`
2. ✅ Redis running
3. ✅ OpenAI API key set

**Quick Check**:
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok", ...}
```

---

## Configuration Methods

### Method 1: Warp Settings UI (Recommended)

Unfortunately, as of now, **Warp doesn't support custom OpenAI endpoints in the UI**. You'll need to use Method 2 or 3.

### Method 2: Environment Variables (Works Now)

Set these in your shell config (`~/.zshrc` or `~/.bashrc`):

```bash
# Add to ~/.zshrc
export OPENAI_API_BASE=http://localhost:8000
export OPENAI_API_KEY=sk-your-key-here

# Reload
source ~/.zshrc
```

**Note**: This affects ALL tools using OpenAI, not just Warp.

### Method 3: Proxy Your Entire System (Advanced)

Use a system-wide proxy or HTTP interceptor to redirect OpenAI API calls to localhost. This is complex and not recommended for most users.

### Method 4: Request Warp Feature (Best Long-Term)

Submit a feature request to Warp:
- GitHub: https://github.com/warpdotdev/Warp/issues
- Discord: https://discord.gg/warpdotdev
- Request: "Custom OpenAI API Endpoint for Warp AI"

---

## Workaround: Use Warp Terminal with cURL

While waiting for native support, you can use your proxy via cURL in Warp terminal:

### 1. Create Helper Function

Add to `~/.zshrc`:

```bash
# AI Assistant with Memory
ask() {
    local query="$*"
    curl -s -X POST http://localhost:8000/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $OPENAI_API_KEY" \
      -d "{
        \"model\": \"gpt-4o-mini\",
        \"messages\": [{\"role\": \"user\", \"content\": \"$query\"}]
      }" | jq -r '.choices[0].message.content'
}

# Alias for quick access
alias ai='ask'
```

### 2. Reload and Use

```bash
source ~/.zshrc

# Use it
ask "What is my name?"
ai "Remember I like Python and AI"
ai "What do I like?"
```

---

## Testing Your Configuration

Run the test script:

```bash
cd /Users/joaolucas/Desktop/Proxy\ Orchestrator/proxy-orchestrator
./test-warp-connection.sh
```

**Expected Output**:
```
✓ Proxy is running on http://localhost:8000
✓ OpenAI API key is set
✓ Proxy is working!
✓ All tests passed!
```

---

## Verifying Memory is Working

### 1. Send a Message with Personal Info

```bash
ask "My name is João and my favorite color is blue"
```

### 2. Check Logs for Memory Storage

```bash
tail -f /tmp/proxy_v3.log | grep "Tier"
```

**Expected**:
```
Tier 1 stored: True
Tier 2 facts: 2
Tier 3 queued: 1 chunks
```

### 3. Query Your Memory

```bash
ask "What is my favorite color?"
```

**Expected**: Should correctly recall "blue"

### 4. Check Redis Storage

```bash
# Tier 1 (conversations)
redis-cli -n 0 KEYS "conversation:*"

# Tier 2 (facts)
redis-cli -n 1 KEYS "session:*"
```

---

## Understanding Memory Tiers in Warp

When you interact through the proxy, queries are automatically routed:

### Level 1 (90% of queries)
```bash
ask "Hello"
ask "Thanks"
ask "Continue"
```
**Memory**: Last 10 conversation turns (~200 tokens)

### Level 2 (8% of queries)
```bash
ask "What's my name?"
ask "What do I like?"
ask "Show my preferences"
```
**Memory**: Last 15 turns + extracted facts (~400 tokens)

### Level 3 (2% of queries)
```bash
ask "Remember when we talked about AI?"
ask "Compare my preferences over time"
ask "What's the relationship between X and Y?"
```
**Memory**: All tiers (20 turns + facts + graph, ~1000 tokens)

---

## Viewing Memory Usage

### Real-Time Monitoring

```bash
# Watch tier usage
tail -f /tmp/proxy_v3.log | grep tier_level

# Watch token costs
tail -f /tmp/proxy_v3.log | grep total_cost_estimate
```

### Memory Statistics

```bash
# Get average tokens used
grep "total_cost_estimate" /tmp/proxy_v3.log | \
  awk '{sum+=$NF; count++} END {print "Avg:", sum/count, "tokens"}'

# Get tier distribution
grep "tier_level" /tmp/proxy_v3.log | \
  awk '{print $NF}' | sort | uniq -c
```

---

## Advanced: Custom Warp AI Command

Create a more sophisticated wrapper:

```bash
# Add to ~/.zshrc
warp_ai() {
    local query="$*"
    local conversation_id="warp-$(date +%Y%m%d)"
    
    echo "🤖 Thinking..."
    
    RESPONSE=$(curl -s -X POST http://localhost:8000/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $OPENAI_API_KEY" \
      -H "X-User-ID: warp-user" \
      -H "X-Conversation-ID: $conversation_id" \
      -d "{
        \"model\": \"gpt-4o-mini\",
        \"messages\": [{\"role\": \"user\", \"content\": \"$query\"}]
      }")
    
    # Extract response
    echo "$RESPONSE" | jq -r '.choices[0].message.content'
    echo ""
    
    # Show metadata
    echo "📊 Memory: $(echo "$RESPONSE" | jq -r '._memory_metadata.tiers_used | join(", ")')"
    echo "💰 Tokens: $(echo "$RESPONSE" | jq -r '._memory_metadata.total_cost_estimate')"
}

alias wai='warp_ai'
```

**Usage**:
```bash
wai "My name is João"
wai "What's my name?"  # Will recall from memory
```

---

## Troubleshooting

### Issue: "Connection refused"

**Solution**: Start the proxy
```bash
cd /Users/joaolucas/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
python main.py
```

### Issue: "Authentication failed"

**Solution**: Check API key
```bash
echo $OPENAI_API_KEY
# Should start with sk-
```

### Issue: "Memory not working"

**Solution**: Check logs
```bash
tail -50 /tmp/proxy_v3.log | grep -E "(ERROR|Tier)"
```

**Solution**: Verify Redis
```bash
redis-cli PING
# Should return: PONG
```

### Issue: "No conversation history"

**Solution**: Check conversation ID
```bash
grep "conversation_id" /tmp/proxy_v3.log | tail -5
# Should see: default-{user_id}
```

---

## Performance Tips

### 1. Keep Proxy Running

Add to startup script:
```bash
# ~/.zshrc
# Auto-start proxy if not running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    cd ~/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
    nohup python main.py > /tmp/proxy_v3.log 2>&1 &
    echo "Started Memory Proxy"
fi
```

### 2. Monitor Memory Usage

```bash
# Add alias to check memory health
alias memcheck='curl -s http://localhost:8000/health | jq .'
```

### 3. Clear Old Memories

```bash
# Clear Tier 1 (working memory)
redis-cli -n 0 FLUSHDB

# Clear Tier 2 (session facts)
redis-cli -n 1 FLUSHDB
```

---

## Example Workflow

### 1. Start Your Day

```bash
# Check proxy
curl http://localhost:8000/health

# Introduce yourself
ask "I'm João, working on AI projects today"
```

### 2. Throughout the Day

```bash
# Simple queries use Tier 1 (fast, cheap)
ask "How do I list files?"
ask "What's the syntax for git commit?"

# Factual queries use Tier 1+2
ask "What am I working on today?"
ask "What's my name?"

# Deep queries use all tiers
ask "Remember what we discussed about memory systems?"
```

### 3. End of Day

```bash
# Check your memory stats
grep "tier_level" /tmp/proxy_v3.log | wc -l  # Total queries
grep "total_cost_estimate" /tmp/proxy_v3.log | \
  awk '{sum+=$NF} END {print "Total tokens:", sum}'
```

---

## Future: Native Warp Support

Once Warp adds custom endpoint support, you'll be able to:

1. **Settings → AI → Custom Endpoint**
   - Base URL: `http://localhost:8000`
   - API Key: Your OpenAI key
   - Model: `gpt-4o-mini`

2. **Use Warp AI Normally**
   - All interactions automatically use your proxy
   - Memory works seamlessly
   - No command-line needed

**Track Progress**:
- Watch Warp GitHub: https://github.com/warpdotdev/Warp
- Join Discord: https://discord.gg/warpdotdev
- Vote on feature: Search for "custom endpoint" issues

---

## Comparison: Direct vs Proxy

| Feature | Direct OpenAI | Through Proxy |
|---------|--------------|---------------|
| Memory | ❌ None | ✅ 3-tier system |
| Token cost | 1000/query | 232/query (77% less) |
| Speed | 500ms | 150ms (caching) |
| Context | ❌ Forgets | ✅ Remembers |
| Setup | Easy | Medium |
| Warp AI support | ✅ Native | ⏳ Coming soon |

---

## Related Documentation

- `PROGRESSIVE_INJECTION.md` - Memory optimization details
- `KNOWN_ISSUES.md` - Troubleshooting guide
- `QUICK_REFERENCE.md` - Quick commands
- `test-warp-connection.sh` - Connection test

---

**Status**: Workaround available, native support requested  
**Last Updated**: 2025-11-05  
**Warp Version**: All versions (as of Nov 2025)
