# AI Commands - Quick Reference

Your Memory-Powered AI Assistant is now set up! 🎉

## 🚀 Available Commands

### `ai "your question"`
Enhanced version with memory metadata
```bash
ai "What is my name?"
ai "Remember I love Python"
ai "What do I like?"
```

**Shows**:
- AI response
- Memory tiers used
- Token cost

### `ask "your question"` or `aiq "your question"`
Quick version (no metadata)
```bash
ask "How do I list files?"
aiq "What's 2+2?"
```

**Shows**:
- AI response only (faster)

### `memcheck`
Check proxy health
```bash
memcheck
```

**Shows**:
- Proxy status
- Memory enabled
- Service version

---

## 💡 Example Usage

### Store Information
```bash
ai "My favorite color is blue and I work on AI projects"
# Response: Got it! I'll remember that...
# 💾 Memory: working_memory, session_facts | 💰 Tokens: 400
```

### Recall Information
```bash
ai "What's my favorite color?"
# Response: Your favorite color is blue.
# 💾 Memory: working_memory, session_facts | 💰 Tokens: 300
```

### Deep Queries
```bash
ai "Remember when we talked about my projects?"
# Uses all 3 memory tiers for complete context
# 💾 Memory: working_memory, session_facts, graphiti | 💰 Tokens: 1000
```

### Simple Queries
```bash
ask "What is 2+2?"
# Fast, minimal memory usage
# Response: 4
```

---

## 🎯 How It Works

### Query Classification

**Simple queries** → Tier 1 only (10 turns, ~200 tokens)
```bash
ask "Hello"
ask "Thanks"
ask "Help me with..."
```

**Factual queries** → Tier 1 + 2 (15 turns + facts, ~400 tokens)
```bash
ai "What's my name?"
ai "What do I like?"
ai "Tell me about myself"
```

**Deep queries** → All tiers (20 turns + facts + graph, ~1000 tokens)
```bash
ai "Remember when we talked about...?"
ai "Compare my preferences over time"
ai "What's the relationship between X and Y?"
```

---

## 📊 Monitoring

### View Real-Time Memory Usage
```bash
tail -f /tmp/proxy_v3.log | grep tier_level
```

### Check Average Token Cost
```bash
grep "total_cost_estimate" /tmp/proxy_v3.log | \
  awk '{sum+=$NF; count++} END {print "Avg:", sum/count, "tokens"}'
```

### See Tier Distribution
```bash
grep "tier_level" /tmp/proxy_v3.log | \
  awk '{print $NF}' | sort | uniq -c
```

Expected: ~90% Level 1, ~8% Level 2, ~2% Level 3

### Check Redis Storage
```bash
# Conversations (Tier 1)
redis-cli -n 0 KEYS "conversation:*"

# Facts (Tier 2)
redis-cli -n 1 KEYS "session:*"
```

---

## 🔧 Management

### Start Proxy (if not running)
```bash
cd ~/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
python main.py
```

### Check Proxy Status
```bash
memcheck
# or
curl http://localhost:8000/health
```

### Clear Memories

**Clear working memory** (Tier 1):
```bash
redis-cli -n 0 FLUSHDB
```

**Clear session facts** (Tier 2):
```bash
redis-cli -n 1 FLUSHDB
```

**Clear all memories**:
```bash
redis-cli FLUSHALL
```

---

## 💰 Cost Savings

### Before (Direct OpenAI)
- Average: 1000 tokens per query
- No memory
- No context

### After (With Proxy)
- Average: 232 tokens per query
- Full memory across sessions
- Intelligent context injection
- **77% cost reduction!**

---

## 🐛 Troubleshooting

### Command not found
```bash
source ~/.zshrc
```

### Connection refused
```bash
# Start proxy
cd ~/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
python main.py &
```

### Memory not working
```bash
# Check logs
tail -50 /tmp/proxy_v3.log

# Check Redis
redis-cli PING

# Check proxy
memcheck
```

---

## 📚 Advanced Tips

### Daily Conversation Context
Create a daily conversation ID:
```bash
alias ai-today='curl -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "X-Conversation-ID: daily-$(date +%Y%m%d)" \
  -d "{\"model\": \"gpt-4o-mini\", \"messages\": [{\"role\": \"user\", \"content\": \"$1\"}]}" | jq -r ".choices[0].message.content"'
```

### Project-Specific Memory
```bash
export AI_PROJECT="memory-system"
ai "Working on $AI_PROJECT today"
```

### Pipe to AI
```bash
cat error.log | jq -Rs '.' | xargs -I {} ai "Analyze this error: {}"
```

---

## 🎓 Learning Examples

### 1. Learn a new topic
```bash
ai "Explain Kubernetes to me"
# Later...
ai "What did we discuss about Kubernetes?"
```

### 2. Track your work
```bash
ai "Today I fixed the backend config scoping bug"
ai "Implemented progressive injection"
# Later...
ai "What did I accomplish today?"
```

### 3. Personal assistant
```bash
ai "Remind me: my meeting is at 3pm"
# Later...
ai "When is my meeting?"
```

---

## 🔗 Related Files

- `WARP_INTEGRATION.md` - Full integration guide
- `PROGRESSIVE_INJECTION.md` - How memory optimization works
- `KNOWN_ISSUES.md` - Troubleshooting
- `test-warp-connection.sh` - Test script

---

**Version**: 1.0  
**Last Updated**: 2025-11-05  
**Status**: ✅ Ready to use!

## Quick Reference Card

```bash
# Ask something
ai "your question"

# Quick ask
ask "your question"

# Check health
memcheck

# View logs
tail -f /tmp/proxy_v3.log

# Clear memory
redis-cli -n 0 FLUSHDB  # Tier 1
redis-cli -n 1 FLUSHDB  # Tier 2
```

**Enjoy your memory-powered AI! 🚀**
