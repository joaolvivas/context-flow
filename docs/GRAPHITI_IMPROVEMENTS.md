# 🧠 Graphiti Memory Improvements

Based on Context7 documentation research and production testing.

---

## 🐛 Critical Bug Fixed (v3.1.1)

**Issue:** Tier 3 (Graphiti) was returning 0 results despite having data in Neo4j.

**Root Cause:** The Graphiti HTTP wrapper requires both `user_id` AND `group_id` parameters, but we were only sending `user_id`.

**Fix Applied:**
```python
# Before (broken)
json={
    "query": query,
    "user_id": user_id,
    "limit": limit
}

# After (working)
json={
    "query": query,
    "user_id": user_id,
    "group_id": user_id,  # Use user_id as group_id for memory namespace
    "limit": limit
}
```

**Also Improved:**
- Increased search limit from 3 → 10 results for better recall

---

## 📊 Current State (After Fix)

### What's Working
✅ Tier 1 (Working Memory): Redis, <1ms latency  
✅ Tier 2 (Session Facts): AI-extracted facts, ~5ms  
✅ Tier 3 (Knowledge Graph): Neo4j + Graphiti, NOW RETURNING RESULTS  

### Test Results
```bash
curl -X POST http://localhost:5001/mcp/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Lucas professional background companies ecommerce",
    "user_id": "lucas-ai",
    "group_id": "lucas-ai",
    "limit": 10
  }'

# Returns 10 relevant memories (was returning 0 before fix)
```

---

## 🚀 Recommended Improvements (Next Steps)

Based on Graphiti best practices from Context7:

### 1. **Implement Center Node Reranking**

**Why:** Rerank results based on graph distance from user's node for more contextually relevant results.

**How:**
```python
# First, get or create user's node UUID
async def get_user_node_uuid(user_id: str):
    results = await graphiti.search_(
        query=user_id,
        config=NODE_HYBRID_SEARCH_EPISODE_MENTIONS,
        group_ids=[user_id]
    )
    return results.nodes[0].uuid if results.nodes else None

# Then use it as center for searches
user_node = await get_user_node_uuid("lucas-ai")

results = await graphiti.search(
    query="What companies did Lucas work for?",
    center_node_uuid=user_node,  # ⭐ Key improvement
    group_ids=["lucas-ai"],
    num_results=10
)
```

**Benefit:** Facts closer to Lucas's node (more personal/relevant) rank higher than distant facts.

---

### 2. **Use Advanced Search Configs**

**Current:** Basic hybrid search  
**Recommended:** Use Graphiti's search recipes for better ranking

```python
from graphiti_core.search.search_config_recipes import (
    NODE_HYBRID_SEARCH_RRF,  # Reciprocal Rank Fusion
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,  # Cross-encoder reranking
    EDGE_HYBRID_SEARCH_RRF
)

# For deep queries about user background
node_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
node_config.limit = 10

results = await graphiti.search_(
    query="Lucas professional background",
    config=node_config,
    group_ids=["lucas-ai"]
)
```

**Search Config Options:**
- `NODE_HYBRID_SEARCH_RRF`: Best for finding specific entities (people, companies)
- `EDGE_HYBRID_SEARCH_RRF`: Best for finding relationships/facts
- `COMBINED_HYBRID_SEARCH_CROSS_ENCODER`: Best overall quality (slower)

---

### 3. **Search Both Nodes AND Edges**

**Current:** We search for edges (facts) only  
**Recommended:** Search nodes (entities) first, then edges (relationships)

```python
# Step 1: Find relevant entities (nodes)
node_results = await graphiti.search_(
    query="companies Lucas worked for",
    config=NODE_HYBRID_SEARCH_RRF,
    group_ids=["lucas-ai"]
)

# Extract company names/entities
companies = [node.name for node in node_results.nodes if "Company" in node.labels]

# Step 2: Find facts about those entities
edge_results = await graphiti.search_(
    query=f"Lucas work experience at {', '.join(companies)}",
    config=EDGE_HYBRID_SEARCH_RRF,
    group_ids=["lucas-ai"]
)

# Combine both
full_context = {
    "entities": node_results.nodes,
    "facts": edge_results.edges
}
```

**Benefit:** More comprehensive context - entities + their relationships

---

### 4. **Add Temporal Filters**

**Use Case:** "What companies have I worked for in the last 2 years?"

```python
from datetime import datetime, timezone, timedelta
from graphiti_core.search.search_filters import SearchFilters

now = datetime.now(timezone.utc)
two_years_ago = now - timedelta(days=730)

search_filter = SearchFilters(
    entity_labels=["Company", "Job"],
    valid_after=two_years_ago,
    valid_before=now
)

results = await graphiti.search(
    query="Lucas work experience",
    group_ids=["lucas-ai"],
    num_results=15,
    search_filter=search_filter
)
```

**Benefit:** Time-aware retrieval for recency-focused queries

---

### 5. **Build and Use Communities**

**Why:** Hierarchical organization for large knowledge graphs

```python
# Build communities (run periodically, not per-query)
communities, edges = await graphiti.build_communities(
    group_ids=["lucas-ai"]
)

# Then search leverages community structure automatically
results = await graphiti.search(
    query="Lucas professional network",
    group_ids=["lucas-ai"],
    num_results=10
)
```

**Benefit:** Better organization for large memory graphs (1000+ facts)

---

### 6. **Retrieve Historical Episodes**

**Use Case:** "Show me our last 10 conversations"

```python
from graphiti_core.nodes import EpisodeType

episodes = await graphiti.retrieve_episodes(
    reference_time=datetime.now(timezone.utc),
    last_n=10,
    group_ids=["lucas-ai"],
    source=EpisodeType.message
)

for episode in episodes:
    print(f"{episode.name}: {episode.content[:100]}...")
```

**Benefit:** Direct access to conversation history without semantic search

---

## 📋 Implementation Priority

### Phase 1: Critical (✅ DONE)
- [x] Fix `group_id` parameter bug
- [x] Increase result limit to 10

### Phase 2: High Impact (Recommended Next)
- [ ] Implement center node reranking
- [ ] Use advanced search configs (RRF/Cross-encoder)
- [ ] Search both nodes and edges

### Phase 3: Advanced Features
- [ ] Add temporal filters
- [ ] Implement community building
- [ ] Add episode retrieval for conversation history

---

## 🧪 Testing the Improvements

### Before Fix
```bash
# Returned 0 results
"memories_retrieved": 0
```

### After Fix
```bash
# Now returns actual memories
curl -X POST http://localhost:5001/mcp/search \
  -d '{"query": "Lucas", "user_id": "lucas-ai", "group_id": "lucas-ai", "limit": 10}'

# Returns:
{
  "results": [
    {"content": "Lucas foca 80-90% do tempo em job applications e networking como Media Buyer"},
    {"content": "Lucas works on AI memory systems"},
    {"content": "Lucas loves building AI agents"},
    ... (10 total results)
  ]
}
```

### Expected After Phase 2 Improvements
- **Better relevance:** Professional facts ranked higher than casual mentions
- **More context:** Both entities (companies, people) and facts (relationships, events)
- **Smarter ranking:** Results closer to user's node score higher

---

## 💡 Key Learnings

1. **Always test integration endpoints directly** - We caught this by testing the Graphiti wrapper separately
2. **Parameter mismatches are silent failures** - The search "worked" but returned 0 results instead of erroring
3. **Search config matters** - Default search is good, but specialized configs are much better
4. **Graph structure helps retrieval** - Center node reranking uses graph topology for relevance

---

## 📚 References

- Graphiti Docs: https://github.com/getzep/graphiti
- Search Examples: `/getzep/graphiti` on Context7
- Best Practices: See code snippets above (all from production Graphiti examples)

---

**Status:** Phase 1 Complete ✅  
**Next:** Implement Phase 2 improvements for even better memory recall  
**Version:** 3.1.1
