# 3-Tier Memory Architecture

## Overview

An intelligent, cost-efficient memory system inspired by human memory:
- **Working Memory**: Recent conversation (instant, zero cost)
- **Session Memory**: Extracted facts (fast, low cost)
- **Long-term Memory**: Knowledge graph (deep, higher cost)

## Architecture

```
┌─────────────────────────────────────────────────┐
│ Tier 1: Working Memory (Redis DB 0)             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Purpose: Conversation continuity                │
│ Storage: Last 20 turns                          │
│ TTL: 30 minutes                                 │
│ Retrieval: ~1ms                                 │
│ Cost: 0 tokens (just storage retrieval)         │
│ Query: Always used                              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Tier 2: Session Memory (Redis DB 1)             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Purpose: Fast fact retrieval                    │
│ Storage: Key facts extracted by gpt-4o-mini     │
│ TTL: 24 hours                                   │
│ Extraction: 1-2s with ~500 tokens              │
│ Retrieval: ~5ms (Redis search)                  │
│ Cost: ~100 tokens per retrieval                 │
│ Query: For factual/personal questions           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Tier 3: Long-term Memory (Graphiti + Neo4j)     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Purpose: Knowledge graph & relationships        │
│ Storage: Entities, relationships, rich context  │
│ TTL: Permanent                                  │
│ Processing: 15-30s with gpt-4o                  │
│ Retrieval: ~1s (graph query + embedding search) │
│ Cost: ~500-2000 tokens per retrieval            │
│ Query: Only for deep/historical questions       │
└─────────────────────────────────────────────────┘
```

## Query Routing Strategy

The `MemoryRouter` intelligently decides which tier(s) to query:

### Always Use: Tier 1 (Working Memory)
- Provides conversation context
- Zero cost, instant retrieval
- Essential for continuity

### Use for Factual Queries: Tier 2 (Session Facts)
Triggered by patterns like:
- "What is my..."
- "Who is..."
- "My favorite..."
- Questions with personal pronouns
- Short queries (<15 words)

**Example:**
```
User: "What's my dog's name?"
→ Uses: Tier 1 + Tier 2
→ Cost: ~300 tokens
→ Time: ~50ms
```

### Use for Deep Queries: Tier 3 (Graphiti)
Triggered by patterns like:
- "Remember when..."
- "What was the relationship between..."
- "Compare X and Y"
- "How long have I..."

**Example:**
```
User: "Remember when we discussed my project ideas last month?"
→ Uses: Tier 1 + Tier 2 + Tier 3
→ Cost: ~800 tokens
→ Time: ~1.5s
```

## Cost Comparison

### Traditional Approach (Only Graphiti):
```
Every query:
- Search: ~500-1000 tokens
- Storage: ~15-30s processing
- Total: High cost, slow responses
```

### 3-Tier Approach:
```
Simple factual query ("What's my favorite color?"):
- Tier 1: 0 tokens (working memory)
- Tier 2: 100 tokens (session facts)
- Total: 100 tokens, <100ms ✅

Deep query ("Remember my project from last month?"):
- Tier 1: 0 tokens
- Tier 2: 100 tokens
- Tier 3: 500 tokens (graphiti)
- Total: 600 tokens, ~1.5s ✅
```

**Savings: 50-80% token reduction for most queries!**

## Usage

### Initialize Memory System

```python
from modules.memory import WorkingMemory, SessionMemory
from modules.memory.intelligent_router import MemoryRouter

# Initialize tiers
working_memory = WorkingMemory(
    redis_host="localhost",
    max_turns=20,
    ttl_seconds=1800  # 30 min
)

session_memory = SessionMemory(
    redis_db=1,
    openai_api_key=your_api_key,
    model="gpt-4o-mini",
    ttl_seconds=86400  # 24 hours
)

# Create router
router = MemoryRouter(
    working_memory=working_memory,
    session_memory=session_memory,
    graphiti_enabled=True
)
```

### Retrieve Memory Context

```python
# Get appropriate context for query
context, metadata = router.get_memory_context(
    user_id="user123",
    conversation_id="conv456",
    query="What's my dog's name?",
    graphiti_search_func=graphiti_backend.search  # Optional
)

print(metadata)
# {
#     "tiers_used": ["working_memory", "session_facts"],
#     "working_memory_turns": 10,
#     "session_facts": 3,
#     "graphiti_memories": 0,
#     "total_cost_estimate": 300
# }
```

### Store Conversation

```python
# Store across tiers
storage_metadata = router.store_conversation_turn(
    user_id="user123",
    conversation_id="conv456",
    user_message="My dog's name is Max",
    assistant_response="Great! Max is a wonderful name.",
    extract_facts=True  # Extract facts to Tier 2
)

print(storage_metadata)
# {
#     "working_memory_stored": True,
#     "session_facts_extracted": 1,
#     "graphiti_queued": True
# }
```

## Benefits

### 🚀 Performance
- **90% of queries**: <100ms (Tier 1+2 only)
- **10% of queries**: ~1.5s (all tiers)
- No 15-30s waits for simple questions!

### 💰 Cost Efficiency
- **50-80% token reduction**
- Pay for deep queries only when needed
- Working memory is completely free

### 🎯 Accuracy
- Working memory: Perfect conversation recall
- Session facts: Quick personal info
- Graphiti: Deep relationships when needed

### 🛡️ Reliability
- Multiple fallback layers
- Redis failures don't break system
- Graceful degradation

## Configuration

### Working Memory (Tier 1)
```python
WorkingMemory(
    max_turns=20,        # Conversation window
    ttl_seconds=1800     # 30 minutes default
)
```

### Session Memory (Tier 2)
```python
SessionMemory(
    model="gpt-4o-mini",    # Fast extraction model
    ttl_seconds=86400       # 24 hours default
)
```

### Memory Router
```python
MemoryRouter(
    graphiti_enabled=True,  # Toggle Tier 3
)
```

## Monitoring

```python
# Check system health
stats = router.get_stats()
# {
#     "working_memory_healthy": True,
#     "session_memory_healthy": True,
#     "graphiti_enabled": True
# }

# Get detailed metadata from each query
context, metadata = router.get_memory_context(...)
print(f"Tiers used: {metadata['tiers_used']}")
print(f"Estimated cost: {metadata['total_cost_estimate']} tokens")
```

## Migration Path

### Phase 1: Enable Working Memory (Immediate benefit)
- Add to existing proxy
- Zero cost, instant context
- Compatible with current Graphiti

### Phase 2: Add Session Memory (Week 1)
- Extract facts in background
- Reduce Graphiti queries by 50%
- Fast personal info retrieval

### Phase 3: Optimize Graphiti (Week 2)
- Query only for deep questions
- Reduce graph context window
- 80% token savings achieved

## Maintenance

### Redis Management
```bash
# Start Redis
brew services start redis

# Check status
redis-cli ping

# Clear memory (if needed)
redis-cli FLUSHDB
```

### Monitoring
```bash
# Watch Redis memory usage
redis-cli INFO memory

# Monitor query patterns
tail -f /tmp/proxy.log | grep "tiers_used"
```

## Future Enhancements

1. **Vector search in Tier 2**: Add embedding-based semantic search
2. **Fact deduplication**: Merge similar facts automatically
3. **Adaptive routing**: Learn which tier works best per user
4. **Cross-conversation facts**: Share facts across conversations
5. **Compression**: Summarize old conversation turns
