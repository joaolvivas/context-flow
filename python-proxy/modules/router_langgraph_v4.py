"""
Memory Router V4 - LangGraph Orchestrated Agent with LangMem

Agent-based orchestration using LangGraph + LangMem for intelligent memory routing.

Architecture:
- Entry Node: Parse OpenAI-compatible request
- Classify Node: Determine memory tier requirements (preserves intelligent routing)
- Parallel Retrieval: Fetch from LangMem namespaces concurrently
- Context Adapter: Optimize context by model (GPT-4o vs local) + filter negatives
- Generate Node: Route to LLM (local/cloud)
- Output Node: Format OpenAI-compatible response + async storage

NEW - LangMem Integration:
- Unified RedisStore with 3 namespaces: conversations, facts, memories
- Semantic vector search (vs keyword matching)
- Native async operations (vs background threads)
- Preserves: query classification, negative filtering, progressive injection

Maintains full compatibility with Msty.ai and existing /v1/chat/completions endpoint.
"""
import os
import asyncio
import logging
from typing import Dict, List, Optional, TypedDict, Annotated, Any
from datetime import datetime
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from modules.router_v3 import (
    get_memory_system,
    route_to_llm,
    enrich_messages_with_tiered_context,
    get_memory_system_prompt,
    is_negative_response,
    filter_negative_content
)
from modules.backends import get_backend
from modules.token_counter import count_message_tokens
from modules.conversation_cache import get_cache
from modules.memory.langmem_store import get_langmem_store  # NEW: LangMem integration

load_dotenv()
logger = logging.getLogger(__name__)


# ============================================================================
# STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """
    State passed between nodes in the LangGraph orchestration.

    This maintains all context needed for memory retrieval, LLM generation,
    and response formatting.
    """
    # Input parameters
    messages: List[Dict]
    model: str
    user_id: str
    conversation_id: str
    provider_url: str
    api_key: str
    temperature: float
    max_tokens: Optional[int]
    stream: bool
    tools: Optional[List[Dict]]
    tool_choice: Optional[Dict]
    functions: Optional[List[Dict]]
    function_call: Optional[Dict]
    extra_params: Dict

    # Memory routing parameters
    memory_enabled: bool
    force_graphiti: bool
    backend_type: str
    backend_config: Dict

    # Query extraction
    query: str

    # Classification results
    classification: Dict

    # Memory retrieval results
    tier1_context: str
    tier2_context: str
    tier3_context: str
    combined_context: str
    optimized_context: str

    # LLM generation
    enriched_messages: List[Dict]
    llm_response: Dict

    # Metadata
    metadata: Dict
    start_time: datetime

    # Output
    final_response: Dict


# ============================================================================
# NODES
# ============================================================================

def entry_node(state: AgentState) -> AgentState:
    """
    Entry node - Initialize state and extract user query.

    This node prepares all initial state needed for downstream processing.
    """
    logger.info("📥 Entry Node: Initializing request")

    # Initialize metadata
    state["metadata"] = {
        "conversation_id": state["conversation_id"],
        "memory_enabled": state["memory_enabled"],
        "tiers_used": [],
        "tier_1_turns": 0,
        "tier_2_facts": 0,
        "tier_3_memories": 0,
        "tokens_input": 0,
        "tokens_output": 0,
        "tokens_memory": 0,
        "processing_time_ms": 0,
        "cache_hit": False,
        "error": None
    }

    # Extract user query from messages
    user_messages = [m for m in state["messages"] if m.get("role") == "user"]
    state["query"] = user_messages[-1]["content"] if user_messages else ""

    # Count original tokens
    original_tokens = count_message_tokens(state["messages"], state["model"])
    state["metadata"]["tokens_input"] = original_tokens

    # Record start time
    state["start_time"] = datetime.now()

    logger.info(f"  Query: {state['query'][:50]}...")
    logger.info(f"  Model: {state['model']}")
    logger.info(f"  User: {state['user_id']}")

    return state


def classify_node(state: AgentState) -> AgentState:
    """
    Classify node - Determine which memory tiers to use.

    Uses MemoryRouter.classify_query to intelligently decide tier activation.
    """
    logger.info("🧠 Classify Node: Analyzing query intent")

    if not state["memory_enabled"] or not state["query"]:
        logger.info("  Memory disabled or no query - skipping classification")
        state["classification"] = {
            "use_working_memory": False,
            "use_session_facts": False,
            "use_graphiti": False,
            "tier_level": 0,
            "search_limit": 0
        }
        return state

    # Get memory system
    memory_router = get_memory_system()

    # Classify query
    classification = memory_router.classify_query(
        state["query"],
        force_graphiti=state.get("force_graphiti", False)
    )

    state["classification"] = classification

    logger.info(f"  Tier Level: {classification['tier_level']}")
    logger.info(f"  Use Working Memory: {classification['use_working_memory']}")
    logger.info(f"  Use Session Facts: {classification['use_session_facts']}")
    logger.info(f"  Use Graphiti: {classification['use_graphiti']}")

    if classification.get("why_tier3"):
        logger.info(f"  Why Tier 3: {classification['why_tier3']}")
        state["metadata"]["why_tier3"] = classification["why_tier3"]

    return state


async def parallel_retrieval_node(state: AgentState) -> AgentState:
    """
    Parallel Retrieval Node - Fetch from all tiers concurrently.

    Executes Tier 1, 2, and 3 retrieval in parallel for minimum latency.
    Supports caching for faster repeated queries.
    """
    logger.info("🔍 Parallel Retrieval Node: Fetching memories")

    classification = state["classification"]

    if classification["tier_level"] == 0:
        logger.info("  No tiers needed - skipping retrieval")
        state["tier1_context"] = ""
        state["tier2_context"] = ""
        state["tier3_context"] = ""
        state["combined_context"] = ""
        return state

    # Check cache first (if enabled)
    cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_hit = False
    memory_metadata = {}

    if cache_enabled:
        try:
            cache = get_cache(
                max_size=int(os.getenv("CACHE_MAX_SIZE", "100")),
                ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "900")),
                similarity_threshold=float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.85"))
            )

            cached_result = cache.get(state["conversation_id"], state["query"], state["model"])
            if cached_result:
                combined_context, memory_metadata = cached_result
                cache_hit = True

                # Parse cached context back into tier contexts
                filtered_combined = filter_negative_content(combined_context)
                state["combined_context"] = filtered_combined
                state["tier1_context"] = ""  # Not separated in cache
                state["tier2_context"] = ""
                state["tier3_context"] = ""

                # Update metadata
                state["metadata"]["cache_hit"] = True
                state["metadata"]["tiers_used"] = memory_metadata.get("tiers_used", [])
                state["metadata"]["tier_1_turns"] = memory_metadata.get("working_memory_turns", 0)
                state["metadata"]["tier_2_facts"] = memory_metadata.get("session_facts", 0)
                state["metadata"]["tier_3_memories"] = memory_metadata.get("graphiti_memories", 0)

                logger.info(f"  ✓ Cache HIT for conversation {state['conversation_id']}")
                return state

        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

    state["metadata"]["cache_hit"] = False

    # NEW: Use LangMemStore instead of manual tiers
    langmem_store = get_langmem_store()
    backend = None
    if classification.get("use_graphiti"):
        try:
            backend = get_backend(
                state.get("backend_type", "graphiti"),
                **(state.get("backend_config") or {})
            )
        except Exception as exc:
            logger.warning(f"Failed to initialize Graphiti backend: {exc}")
            backend = None

    # Define async retrieval functions using LangMemStore
    async def get_tier1():
        """Retrieve recent conversation turns from LangMem (conversations namespace)"""
        if not classification["use_working_memory"]:
            return ""

        raw_context = await langmem_store.format_turns_as_context(
            state["user_id"],
            state["conversation_id"],
            limit=20
        )
        context = filter_negative_content(raw_context)
        turns = await langmem_store.get_recent_turns(
            state["user_id"],
            state["conversation_id"],
            limit=20
        )
        state["metadata"]["tier_1_turns"] = len(turns)
        state["metadata"]["tiers_used"].append("Tier 1 (LangMem Conversations)")

        logger.info(f"  ✓ Tier 1 (LangMem): {len(turns)} turns")
        return context

    async def get_tier2():
        """Retrieve session facts from LangMem (facts namespace) with semantic search"""
        if not classification["use_session_facts"]:
            return "", []

        raw_context = await langmem_store.format_facts_as_context(
            state["user_id"],
            state["conversation_id"],
            query=state["query"],
            limit=10
        )
        context = filter_negative_content(raw_context)
        facts = await langmem_store.search_facts(
            state["user_id"],
            state["conversation_id"],
            state["query"],
            limit=10
        )
        state["metadata"]["tier_2_facts"] = len(facts)
        state["metadata"]["tiers_used"].append("Tier 2 (LangMem Facts)")
        state["metadata"]["tier_2_fact_details"] = facts

        logger.info(f"  ✓ Tier 2 (LangMem): {len(facts)} facts (semantic search)")
        return context, facts

    async def get_tier3():
        """Retrieve long-term memories from LangMem and Graphiti when requested."""
        if not classification["use_graphiti"]:
            return ""

        sections: List[str] = []
        total_memories = 0

        # LangMem (semantic embeddings)
        try:
            memories = await langmem_store.search_memories(
                state["user_id"],
                state["query"],
                limit=classification["search_limit"]
            )
        except Exception as exc:
            logger.warning(f"LangMem Tier3 search failed: {exc}")
            memories = []

        if memories:
            content_blocks = []
            for memory in memories:
                content = memory.get("content", "") or memory.get("metadata", {}).get("summary", "")
                filtered_content = filter_negative_content(content)
                if filtered_content:
                    content_blocks.append(filtered_content)
            if content_blocks:
                sections.append("### LangMem Memories\n" + "\n\n".join(content_blocks))
            total_memories += len(memories)
            state["metadata"]["tiers_used"].append("Tier 3 (LangMem Memories)")
            logger.info(f"  ✓ Tier 3 (LangMem): {len(memories)} memories (semantic search)")

        # Graphiti MCP (knowledge graph)
        graphiti_results: List[Dict[str, Any]] = []
        if backend is not None:
            try:
                search_limit = classification.get("search_limit") or int(os.getenv("GRAPHITI_LANGGRAPH_LIMIT", "5"))
                graphiti_results = backend.search(
                    state["query"],
                    state["user_id"],
                    limit=search_limit
                ) or []
            except Exception as exc:
                logger.warning(f"Graphiti search failed: {exc}")

        if graphiti_results:
            formatted_results = []
            for result in graphiti_results:
                text = (
                    result.get("summary")
                    or result.get("content")
                    or result.get("fact")
                    or result.get("text")
                    or ""
                )
                formatted = filter_negative_content(text.strip())
                if not formatted:
                    continue
                if result.get("metadata"):
                    meta = result["metadata"]
                    entity = meta.get("entity")
                    relation = meta.get("relation")
                    if entity or relation:
                        header_parts = []
                        if entity:
                            header_parts.append(f"Entity: {entity}")
                        if relation:
                            header_parts.append(f"Relation: {relation}")
                        formatted_results.append(f"{'; '.join(header_parts)}\n{formatted}")
                    else:
                        formatted_results.append(formatted)
                else:
                    formatted_results.append(formatted)

            if formatted_results:
                sections.append("### Graphiti Knowledge Graph\n" + "\n\n".join(formatted_results))
                total_memories += len(formatted_results)
                state["metadata"]["tiers_used"].append("Tier 3 (Graphiti)")
                state["metadata"]["graphiti_results"] = len(formatted_results)
                logger.info(f"  ✓ Tier 3 (Graphiti): {len(formatted_results)} results")

        if sections:
            state["metadata"]["tier_3_memories"] = total_memories
            return "\n\n".join(sections)

        return ""
        return ""

    # Execute Tier 1 and Tier 2 retrieval first (can run concurrently)
    tier1_task = asyncio.create_task(get_tier1())
    tier2_task = asyncio.create_task(get_tier2())

    tier1 = await tier1_task
    tier2, tier2_facts = await tier2_task

    # Heuristic: skip Tier 3 for simple factual queries when Tier 1/2 already answer
    tier3 = ""
    skip_tier3 = False
    if (
        classification.get("use_graphiti")
        and not classification.get("force_graphiti")
        and not state.get("force_graphiti")
    ):
        word_limit = int(os.getenv("GRAPHITI_SIMPLE_QUERY_WORD_LIMIT", "12"))
        relevance_threshold = float(os.getenv("GRAPHITI_FACT_CONFIDENCE", "0.88"))
        query_word_count = len(state["query"].split())
        high_conf_fact = any(
            (fact or {}).get("relevance", 0) >= relevance_threshold for fact in tier2_facts
        )
        has_recent_context = bool(tier1.strip())

        if query_word_count <= word_limit and (high_conf_fact or (has_recent_context and tier2_facts)):
            skip_tier3 = True

    if skip_tier3:
        classification["use_graphiti"] = False
        state["metadata"]["why_tier3_skipped"] = "simple_fact_confident"
        logger.info("  ⏭️ Skipping Tier 3: confident answer in Tier 1/2")
    else:
        tier3 = await get_tier3()

    state["tier1_context"] = tier1
    state["tier2_context"] = tier2
    state["tier3_context"] = tier3

    # Combine contexts
    context_parts = []
    if tier1:
        context_parts.append(f"## Recent Conversation\n\n{tier1}")
    if tier2:
        context_parts.append(f"## Session Facts\n\n{tier2}")
    if tier3:
        context_parts.append(f"## Long-term Memories\n\n{tier3}")

    state["combined_context"] = "\n\n".join(context_parts)

    logger.info(f"  Combined context: {len(state['combined_context'])} chars")

    # Store in cache for future queries (if enabled and not a cache hit)
    if cache_enabled and not cache_hit and state["combined_context"]:
        try:
            cache = get_cache(
                max_size=int(os.getenv("CACHE_MAX_SIZE", "100")),
                ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "900")),
                similarity_threshold=float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.85"))
            )

            # Build metadata for cache
            cache_metadata = {
                "tiers_used": state["metadata"]["tiers_used"],
                "working_memory_turns": state["metadata"].get("tier_1_turns", 0),
                "session_facts": state["metadata"].get("tier_2_facts", 0),
                "graphiti_memories": state["metadata"].get("tier_3_memories", 0),
                "graphiti_results": state["metadata"].get("graphiti_results", 0)
            }

            cache.set(
                state["conversation_id"],
                state["query"],
                state["combined_context"],
                cache_metadata,
                state["model"]
            )

            logger.info(f"  ✓ Stored in cache for conversation {state['conversation_id']}")

        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    return state


def context_adapter_node(state: AgentState) -> AgentState:
    """
    Context Adapter Node - Optimize context based on model capabilities.

    Filters negative/unhelpful facts and adapts context size by model type:
    - GPT-4o: Full context (can handle 3K+ tokens)
    - Local models (Qwen, Mistral): Compressed context (800 tokens max)

    FILTERING STEP:
    - Removes sentences containing "não tenho informação", "does not have information", etc.
    - Prioritizes positive, factual information about the user
    """
    logger.info("⚡ Context Adapter Node: Optimizing for model")

    model = state["model"].lower()
    combined_context = state["combined_context"]

    # Check if model is local or cloud
    is_local = any(name in model for name in ["qwen", "mistral", "llama", "phi"])
    is_gpt4 = "gpt-4" in model or "gpt4" in model

    if not combined_context:
        state["optimized_context"] = ""
        logger.info("  No context to optimize")
        return state

    # STEP 1: FILTER negative/unhelpful facts from ALL tiers
    # This prevents "I don't have information..." from polluting context
    tier1_filtered = filter_negative_content(state["tier1_context"])
    tier2_filtered = filter_negative_content(state["tier2_context"])
    tier3_filtered = filter_negative_content(state["tier3_context"])

    # Reconstruct combined context with filtered tiers
    filtered_parts = []
    if tier1_filtered:
        filtered_parts.append(f"## Recent Conversation\n\n{tier1_filtered}")
    if tier2_filtered:
        filtered_parts.append(f"## Session Facts\n\n{tier2_filtered}")
    if tier3_filtered:
        filtered_parts.append(f"## Long-term Memories\n\n{tier3_filtered}")

    filtered_combined = "\n\n".join(filtered_parts)

    # Log filtering results
    original_chars = len(combined_context)
    filtered_chars = len(filtered_combined)
    if filtered_chars < original_chars:
        removed = original_chars - filtered_chars
        logger.info(f"  🧹 Filtered out {removed} chars of negative content")
    else:
        logger.info(f"  ✓ No negative content detected")

    # STEP 2: Adapt context size based on model type
    if is_gpt4:
        # GPT-4o can handle full context
        state["optimized_context"] = filtered_combined
        logger.info(f"  GPT-4o: Using full filtered context ({len(filtered_combined)} chars)")

    elif is_local:
        # Local models need compressed context
        # Work with FILTERED tiers to avoid negative content
        # Simple compression: take first 3000 chars (roughly 800 tokens)
        max_chars = 3000

        if len(filtered_combined) > max_chars:
            # Prioritize recent context (Tier 1) over historical (Tier 3)
            # Use FILTERED tiers (already cleaned)
            tier1 = tier1_filtered
            tier2 = tier2_filtered
            tier3 = tier3_filtered

            # Budget allocation: Tier 1 (40%), Tier 2 (30%), Tier 3 (30%)
            t1_budget = int(max_chars * 0.4)
            t2_budget = int(max_chars * 0.3)
            t3_budget = int(max_chars * 0.3)

            compressed_parts = []
            if tier1:
                compressed_parts.append(tier1[:t1_budget])
            if tier2:
                compressed_parts.append(tier2[:t2_budget])
            if tier3:
                compressed_parts.append(tier3[:t3_budget])

            state["optimized_context"] = "\n\n".join(compressed_parts)

            logger.info(f"  Local model: Compressed filtered context {len(filtered_combined)} → {len(state['optimized_context'])} chars")
        else:
            state["optimized_context"] = filtered_combined
            logger.info(f"  Local model: Filtered context within limit ({len(filtered_combined)} chars)")

    else:
        # Other cloud models (Claude, etc) - use full FILTERED context
        state["optimized_context"] = filtered_combined
        logger.info(f"  Cloud model: Using full filtered context ({len(filtered_combined)} chars)")

    # Add context preview to metadata
    preview = state["optimized_context"][:200].replace("\n", " ")
    state["metadata"]["context_preview"] = preview

    return state


def generate_node(state: AgentState) -> AgentState:
    """
    Generate Node - Call LLM with enriched context.

    Routes to local or cloud model based on api_key and provider_url.
    """
    logger.info("🤖 Generate Node: Calling LLM")

    # Enrich messages with optimized context
    if state["optimized_context"]:
        enriched = enrich_messages_with_tiered_context(
            state["messages"],
            state["optimized_context"]
        )
    else:
        enriched = state["messages"]

    state["enriched_messages"] = enriched

    # Count memory tokens
    if state["optimized_context"]:
        state["metadata"]["tokens_memory"] = len(state["optimized_context"].split())

    logger.info(f"  Routing to: {state['provider_url']}")
    logger.info(f"  Model: {state['model']}")

    # Call LLM via router_v3's route_to_llm
    try:
        response = route_to_llm(
            messages=enriched,
            model=state["model"],
            provider_url=state["provider_url"],
            api_key=state["api_key"],
            temperature=state["temperature"],
            max_tokens=state["max_tokens"],
            stream=state["stream"],
            tools=state.get("tools"),
            tool_choice=state.get("tool_choice"),
            functions=state.get("functions"),
            function_call=state.get("function_call"),
            **state.get("extra_params", {})
        )

        state["llm_response"] = response

        # Extract token usage
        if not state["stream"]:
            usage = response.get("usage", {})
            state["metadata"]["tokens_output"] = usage.get("completion_tokens", 0)

        logger.info("  ✓ LLM response received")

    except Exception as e:
        logger.error(f"  ✗ LLM error: {e}", exc_info=True)
        state["metadata"]["error"] = str(e)

        # Create error response
        state["llm_response"] = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"Error generating response: {str(e)}"
                },
                "finish_reason": "error"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }

    return state


def output_node(state: AgentState) -> AgentState:
    """
    Output Node - Format final OpenAI-compatible response.

    Adds memory metadata for diagnostic headers.
    Stores conversation turn in memory tiers (Tier 1+2+3).
    """
    logger.info("📤 Output Node: Formatting response")

    # Calculate processing time
    processing_time = (datetime.now() - state["start_time"]).total_seconds() * 1000
    state["metadata"]["processing_time_ms"] = processing_time

    # Add metadata to response
    response = state["llm_response"]
    response["_memory_metadata"] = state["metadata"]

    state["final_response"] = response

    logger.info(f"  Processing time: {processing_time:.0f}ms")
    logger.info(f"  Tiers used: {', '.join(state['metadata']['tiers_used']) or 'None'}")

    # Store conversation turn in memory (Tier 1+2+3)
    if state["memory_enabled"] and state["query"] and not state["stream"]:
        _store_conversation_turn_async(state)

    return state


def _store_conversation_turn_async(state: AgentState):
    """
    Store conversation turn using LangMemStore (async, non-blocking).

    NEW in LangMem migration:
    - Uses unified LangMemStore with 3 namespaces (conversations, facts, memories)
    - Semantic vector search instead of keyword matching
    - Native async operations (no threading needed)
    - Preserves negative response filtering
    """
    # Extract assistant response
    assistant_response = state["llm_response"].get("choices", [{}])[0].get("message", {}).get("content", "")

    if not assistant_response:
        logger.warning("No assistant response to store")
        return

    # Truncate very long responses to prevent token limit issues
    max_content_length = 1000
    if len(assistant_response) > max_content_length:
        assistant_response = assistant_response[:max_content_length] + "... [truncated]"

    # Capture variables for closure
    user_id = state["user_id"]
    conversation_id = state["conversation_id"]
    query = state["query"]
    model = state["model"]
    backend_type = state["backend_type"]
    backend_config = state["backend_config"]

    # Store using async LangMemStore (no background thread needed - async is non-blocking)
    async def store_in_langmem():
        try:
            # FILTER: Skip storing negative/unhelpful responses
            if is_negative_response(assistant_response):
                logger.info(f"⚠️ Skipping storage: Response is negative/unhelpful")
                logger.debug(f"Negative response preview: {assistant_response[:100]}...")
                return

            # Get LangMem store
            langmem_store = get_langmem_store()

            # Store Tier 1: Conversation turns (always stored for continuity)
            await langmem_store.add_turn(user_id, conversation_id, "user", query)
            await langmem_store.add_turn(user_id, conversation_id, "assistant", assistant_response)
            logger.info(f"✅ Tier 1 (LangMem): Conversation turns stored")

            # Store Tier 2: Extract and store facts (only if positive response)
            # Use old SessionMemory for fact extraction (LLM-based)
            # Then store extracted facts in LangMem
            try:
                memory_router = get_memory_system()
                facts = memory_router.session_memory.extract_facts(query, assistant_response)

                if facts:
                    facts_stored = await langmem_store.store_facts(user_id, conversation_id, facts)
                    logger.info(f"✅ Tier 2 (LangMem): {facts_stored} facts stored")
                else:
                    logger.info(f"  ℹ️ Tier 2: No facts extracted")

            except Exception as e:
                logger.warning(f"Tier 2 fact extraction error: {e}")

            # Store Tier 3: Long-term semantic memory (only if positive response)
            try:
                memory_content = f"User: {query}\nAssistant: {assistant_response}"
                memory_id = await langmem_store.store_memory(
                    user_id,
                    memory_content,
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "model": model,
                        "conversation_id": conversation_id
                    }
                )
                logger.info(f"✅ Tier 3 (LangMem): Memory stored with ID {memory_id}")

            except Exception as e:
                logger.error(f"Tier 3 storage error: {e}")

        except Exception as e:
            logger.error(f"LangMem storage error: {e}", exc_info=True)

    # Schedule async storage (non-blocking)
    # Try to use the existing event loop, fall back to executor if needed
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, schedule the task
        loop.create_task(store_in_langmem())
        logger.info("💾 LangMem storage scheduled (async task)")
    except RuntimeError:
        # No event loop running, use thread executor
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        executor.submit(lambda: asyncio.run(store_in_langmem()))
        logger.info("💾 LangMem storage scheduled (executor)")


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_memory_graph() -> StateGraph:
    """
    Create the LangGraph orchestration graph.

    Flow:
    Entry → Classify → Parallel Retrieval → Context Adapter → Generate → Output
    """
    logger.info("🔧 Creating LangGraph memory orchestration graph")

    # Create graph with state schema
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("entry", entry_node)
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve", parallel_retrieval_node)
    graph.add_node("adapt_context", context_adapter_node)
    graph.add_node("generate", generate_node)
    graph.add_node("output", output_node)

    # Define edges (linear flow for now)
    graph.add_edge("entry", "classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "adapt_context")
    graph.add_edge("adapt_context", "generate")
    graph.add_edge("generate", "output")
    graph.add_edge("output", END)

    # Set entry point
    graph.set_entry_point("entry")

    logger.info("  ✓ Graph constructed with 6 nodes")

    return graph


# Global graph instance (initialized once)
_memory_graph = None


def get_memory_graph():
    """Get or initialize the memory orchestration graph."""
    global _memory_graph

    if _memory_graph is None:
        graph = create_memory_graph()

        # Use in-memory checkpointer (can be replaced with Redis-based later)
        checkpointer = MemorySaver()

        _memory_graph = graph.compile(checkpointer=checkpointer)

        logger.info("✓ Memory graph compiled and ready")

    return _memory_graph


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def memory_route_langgraph(
    messages: List[Dict],
    model: str,
    user_id: str,
    provider_url: str,
    api_key: str,
    conversation_id: Optional[str] = None,
    backend_type: str = "graphiti",
    backend_config: Optional[Dict] = None,
    memory_enabled: bool = True,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    tools: Optional[List[Dict]] = None,
    tool_choice: Optional[Dict] = None,
    functions: Optional[List[Dict]] = None,
    function_call: Optional[Dict] = None,
    force_graphiti: bool = False,
    **extra_params
) -> Dict:
    """
    LangGraph-based memory routing (V4).

    Drop-in replacement for memory_route_v3 with agent orchestration.

    Args:
        Same as memory_route_v3

    Returns:
        OpenAI-compatible response dict with _memory_metadata
    """
    logger.info("🚀 LangGraph Memory Route V4 - Starting orchestration")

    # Generate conversation ID if not provided
    if not conversation_id:
        conversation_id = f"default-{user_id}"

    # Prepare initial state
    initial_state: AgentState = {
        "messages": messages,
        "model": model,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "provider_url": provider_url,
        "api_key": api_key,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
        "tools": tools,
        "tool_choice": tool_choice,
        "functions": functions,
        "function_call": function_call,
        "extra_params": extra_params,
        "memory_enabled": memory_enabled,
        "force_graphiti": force_graphiti,
        "backend_type": backend_type,
        "backend_config": backend_config or {},
        "query": "",
        "classification": {},
        "tier1_context": "",
        "tier2_context": "",
        "tier3_context": "",
        "combined_context": "",
        "optimized_context": "",
        "enriched_messages": [],
        "llm_response": {},
        "metadata": {},
        "start_time": datetime.now(),
        "final_response": {}
    }

    # Get graph
    graph = get_memory_graph()

    # Execute graph asynchronously (supports async nodes)
    config = {"configurable": {"thread_id": conversation_id}}

    try:
        final_state = await graph.ainvoke(initial_state, config=config)

        logger.info("✓ LangGraph orchestration completed successfully")

        return final_state["final_response"]

    except Exception as e:
        logger.error(f"✗ LangGraph orchestration failed: {e}", exc_info=True)

        # Fallback to simple error response
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"Error in agent orchestration: {str(e)}"
                },
                "finish_reason": "error"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "_memory_metadata": {
                "error": str(e),
                "conversation_id": conversation_id,
                "memory_enabled": memory_enabled
            }
        }
