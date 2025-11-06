# LangMem Migration Plan

## Objetivo

Migrar do gerenciamento manual de memória (3 tiers custom em Redis + Graphiti) para a infraestrutura oficial do LangGraph (LangMem + BaseStore), reduzindo manutenção e aproveitando features nativas do framework.

---

## Arquitetura Atual (Manual)

### Tier 1 - Working Memory
- **Storage:** Redis key-value
- **Conteúdo:** Últimas N conversation turns (raw)
- **TTL:** 30 minutos
- **Código:** `python-proxy/modules/memory/working_memory.py`
- **Uso:** 100% das queries (conversation continuity)

### Tier 2 - Session Memory
- **Storage:** Redis key-value
- **Conteúdo:** Fatos extraídos via LLM (gpt-4o-mini)
- **TTL:** Variável (biografia: 30 dias, schedule: 1 dia)
- **Código:** `python-proxy/modules/memory/session_memory.py`
- **Uso:** ~10% das queries (factual/personal)

### Tier 3 - Graphiti Knowledge Graph
- **Storage:** Neo4j + embeddings
- **Conteúdo:** Entity extraction + relationships
- **TTL:** Permanente
- **Código:** `python-proxy/modules/backends/graphiti_backend.py`
- **Uso:** ~2% das queries (deep/comprehensive)

### Orquestração
- **MemoryRouter** (`intelligent_router.py`): Classifica queries e roteia para tiers apropriados
- **Progressive Injection:** 90% Tier 1 only → 8% Tier 1+2 → 2% All tiers
- **LangGraph V4:** Entry → Classify → Parallel Retrieval → Adapt → Generate → Output

### Heurísticas Manuais
1. Query classification (Simple/Factual/Deep/Comprehensive)
2. Negative response filtering (`is_negative_response()`)
3. Cache semântico (intent-based)
4. TTL policies por categoria
5. Query expansion para comprehensive queries
6. Background storage threads

---

## Arquitetura Nova (LangMem)

### Unified Store (BaseStore + RedisStore)
- **Storage:** Redis com vector search integrado
- **Namespacing:**
  - `("conversations", user_id, conv_id)` → Recent turns
  - `("facts", user_id, conv_id)` → Extracted facts
  - `("memories", user_id)` → Long-term semantic memories
- **Features:**
  - Semantic search com embeddings (OpenAI text-embedding-3-small)
  - JSON document storage
  - Cross-thread persistence
  - Deduplicação automática

### Substituições

| Componente Atual | Substituto LangMem | Ganhos |
|-----------------|-------------------|--------|
| WorkingMemory | RedisStore + namespace `conversations` | Vector search, unificação |
| SessionMemory | RedisStore + namespace `facts` | Semantic search nativo |
| Graphiti Backend | RedisStore + namespace `memories` | Reduz Neo4j dependency |
| Manual storage threads | store.put() / store.search() | API async nativa |
| Custom cache | LangGraph checkpointing | Framework-level caching |

### O que Preservamos

1. **Query Classification (Mantido)**
   - `MemoryRouter.classify_query()` continua
   - Usa classificação para determinar search limits e strategy
   - Progressive injection strategy se mantém

2. **Negative Response Filtering (Mantido)**
   - `is_negative_response()` como hook PRÉ-storage
   - LangMem não tem isso nativo
   - Evita poluição da memória

3. **Intelligent Routing (Mantido)**
   - Deep query → search em múltiplos namespaces
   - Factual query → search apenas em `facts`
   - Simple query → search apenas em `conversations`

4. **Headers & Logs (Mantidos)**
   - `X-Memory-Tiers-Used`, `X-Cache-Status`, etc.
   - Logs de timing e debug

---

## Implementation Strategy

### Phase 1: Add LangMem Dependencies
**File:** `requirements.txt`
```python
langmem==0.1.1  # Official LangMem SDK
langgraph-checkpoint-redis==2.0.0  # Redis store for LangGraph
```

### Phase 2: Create LangMem Store Wrapper
**New File:** `python-proxy/modules/memory/langmem_store.py`

Responsibilities:
- Initialize RedisStore with embeddings config
- Namespace management (conversations, facts, memories)
- Wrapper functions matching current API
- Async put/search operations

```python
class LangMemStore:
    def __init__(self, redis_url: str):
        self.store = RedisStore.from_conn_string(
            redis_url,
            index={
                "dims": 1536,
                "embed": "openai:text-embedding-3-small"
            }
        )

    async def add_turn(self, user_id, conv_id, role, content):
        """Store conversation turn (replaces WorkingMemory)"""
        namespace = ("conversations", user_id, conv_id)
        doc_id = f"turn_{int(time.time()*1000)}"
        await self.store.aput(namespace, doc_id, {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    async def get_recent_turns(self, user_id, conv_id, limit=20):
        """Get recent turns (replaces WorkingMemory.get_recent_turns)"""
        namespace = ("conversations", user_id, conv_id)
        items = await self.store.asearch(namespace, query="", limit=limit)
        return sorted(items, key=lambda x: x.get("timestamp", ""))

    async def store_facts(self, user_id, conv_id, facts):
        """Store extracted facts (replaces SessionMemory)"""
        namespace = ("facts", user_id, conv_id)
        for fact in facts:
            doc_id = f"fact_{int(time.time()*1000)}"
            await self.store.aput(namespace, doc_id, fact)

    async def search_facts(self, user_id, conv_id, query, limit=5):
        """Semantic search over facts"""
        namespace = ("facts", user_id, conv_id)
        return await self.store.asearch(namespace, query=query, limit=limit)

    async def search_memories(self, user_id, query, limit=10):
        """Semantic search in long-term memory (replaces Graphiti)"""
        namespace = ("memories", user_id)
        return await self.store.asearch(namespace, query=query, limit=limit)
```

### Phase 3: Update MemoryRouter
**File:** `python-proxy/modules/memory/intelligent_router.py`

Changes:
- Replace `WorkingMemory` + `SessionMemory` with `LangMemStore`
- Keep `classify_query()` logic UNCHANGED
- Update `get_memory_context()` to use async store operations
- Keep progressive injection strategy

### Phase 4: Update LangGraph V4 Router
**File:** `python-proxy/modules/router_langgraph_v4.py`

Changes:
1. **Compile graph with store:**
   ```python
   from modules.memory.langmem_store import get_langmem_store

   store = get_langmem_store()
   graph = builder.compile(
       checkpointer=checkpointer,  # Existing
       store=store  # NEW - LangMem store
   )
   ```

2. **Update parallel_retrieval_node:**
   - Replace manual Redis calls with `store.asearch()`
   - Use namespaces: `conversations`, `facts`, `memories`
   - Keep cache checking logic

3. **Update output_node:**
   - Replace background thread storage with `store.aput()`
   - Keep negative response filtering BEFORE put
   - Async storage (no threads needed)

4. **BaseStore injection:**
   - LangGraph auto-injects store into nodes
   - Access via `config["store"]` or function parameter

### Phase 5: Preserve Negative Filtering
**File:** `python-proxy/modules/router_v3.py`

Keep functions:
- `is_negative_response(text)` → Used as pre-storage hook
- `filter_negative_content(content)` → Used in context adapter

Integration:
```python
# In output_node, BEFORE storing
if is_negative_response(assistant_response):
    logger.info("⚠️ Skipping storage: negative response")
    return state  # Don't call store.aput()

# Normal storage
await store.aput(namespace, doc_id, {...})
```

### Phase 6: Configuration
**File:** `.env.example`

Add:
```bash
# LangMem Configuration
REDIS_URL=redis://localhost:6379
LANGMEM_EMBEDDING_MODEL=openai:text-embedding-3-small
LANGMEM_EMBEDDING_DIMS=1536

# Memory Namespaces (optional customization)
LANGMEM_CONVERSATIONS_NS=conversations
LANGMEM_FACTS_NS=facts
LANGMEM_MEMORIES_NS=memories
```

### Phase 7: Deprecate Old Files
Mark as deprecated (don't delete yet):
- `python-proxy/modules/memory/working_memory.py`
- `python-proxy/modules/memory/session_memory.py`
- Graphiti backend can stay as fallback

---

## Migration Benefits

### 1. Reduced Manual Code
- **Before:** ~800 lines across 3 memory modules
- **After:** ~200 lines in 1 LangMem wrapper
- **Savings:** 75% reduction in custom code

### 2. Native Features
- Vector search (vs keyword matching in SessionMemory)
- Async operations (vs background threads)
- Checkpointing integration
- Cross-thread persistence

### 3. Improved Performance
- Semantic search > keyword matching
- Unified Redis queries (vs multiple DB calls)
- Framework-level optimizations

### 4. Better Scalability
- Official support for Postgres, MongoDB (not just Redis)
- Production-ready async patterns
- Built-in connection pooling

### 5. Reduced Dependencies
- No need for custom Neo4j (Graphiti) for most use cases
- Redis handles both cache AND long-term memory
- Simpler deployment

---

## Rollout Plan

### Step 1: Install Dependencies
```bash
cd python-proxy
pip install langmem==0.1.1 langgraph-checkpoint-redis==2.0.0
pip install -r requirements.txt
```

### Step 2: Create LangMem Store Module
Implement `python-proxy/modules/memory/langmem_store.py`

### Step 3: Update MemoryRouter (Minimal Changes)
Keep classification, swap storage backend

### Step 4: Update LangGraph V4
- Pass store to compile()
- Update retrieval/storage nodes

### Step 5: Test Locally (User Will Do)
- Verify endpoints work
- Check headers (tiers_used, cache, etc.)
- Validate memory persistence

### Step 6: Monitor & Iterate
- Watch for errors in new storage logic
- Compare response quality vs old system
- Tune search limits if needed

---

## Compatibility Matrix

| Feature | Before | After | Status |
|---------|--------|-------|--------|
| /v1/chat/completions | ✅ | ✅ | Preserved |
| Msty client | ✅ | ✅ | Preserved |
| Local model routing | ✅ | ✅ | Preserved |
| Cloud routing (GPT/Claude) | ✅ | ✅ | Preserved |
| X-Memory-* headers | ✅ | ✅ | Preserved |
| Cache hit rate | ✅ | ✅ | Preserved |
| Negative filtering | ✅ | ✅ | Preserved |
| Query classification | ✅ | ✅ | Preserved |
| Progressive injection | ✅ | ✅ | Preserved |
| Conversation continuity | ✅ | ✅ | Preserved |
| Fact extraction | ✅ | ✅ (Better) | Enhanced |
| Semantic search | ❌ (Keywords) | ✅ (Vectors) | New |
| Cross-thread memory | ❌ | ✅ | New |
| Multiple backends | ❌ (Redis only) | ✅ (Redis/Postgres) | New |

---

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation:** Keep old modules as fallback, feature flag for LangMem

### Risk 2: Performance Regression
**Mitigation:** Benchmark before/after, tune search limits

### Risk 3: Lost Context
**Mitigation:** Export existing Redis data, import to LangMem namespaces

### Risk 4: Embedding Costs
**Mitigation:** Use text-embedding-3-small (cheap), cache embeddings

---

## Next Steps

1. ✅ Research LangMem (DONE)
2. ✅ Analyze current architecture (DONE)
3. ✅ Design migration plan (DONE)
4. ⏳ Implement langmem_store.py module
5. ⏳ Update router_langgraph_v4.py
6. ⏳ Update requirements.txt
7. ⏳ Update .env.example
8. ⏳ Test integration
9. ⏳ Document changes
10. ⏳ Commit & Push

---

## Questions for Review

1. Should we keep Graphiti as fallback for advanced knowledge graph queries?
2. Do we want to migrate existing Redis data to LangMem namespaces?
3. Should we use Postgres instead of Redis for production?
4. Keep fact extraction with LLM, or let LangMem decide what to store?

---

## Summary

This migration will:
- ✅ Eliminate 75% of custom memory code
- ✅ Add semantic search capabilities
- ✅ Preserve all existing features
- ✅ Improve scalability & maintenance
- ✅ Use official LangGraph framework features

**Recommendation:** Proceed with implementation, keeping old modules as fallback for first deploy.
