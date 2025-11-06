"""
Memory Router V4 - LangGraph Orchestrated Agent

Agent-based orchestration using LangGraph for intelligent memory routing.

Architecture:
- Entry Node: Parse OpenAI-compatible request
- Classify Node: Determine memory tier requirements
- Parallel Retrieval: Fetch Tier 1+2+3 concurrently
- Context Adapter: Optimize context by model (GPT-4o vs local)
- Generate Node: Route to LLM (local/cloud)
- Output Node: Format OpenAI-compatible response

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
    get_memory_system_prompt
)
from modules.backends import get_backend
from modules.token_counter import count_message_tokens

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

    memory_router = get_memory_system()

    # Define async retrieval functions
    async def get_tier1():
        if not classification["use_working_memory"]:
            return ""

        context = memory_router.working_memory.format_as_context(
            state["user_id"],
            state["conversation_id"],
            limit=20
        )
        turns = len(memory_router.working_memory.get_recent_turns(
            state["user_id"],
            state["conversation_id"],
            limit=20
        ))
        state["metadata"]["tier_1_turns"] = turns
        state["metadata"]["tiers_used"].append("Tier 1 (Working)")

        logger.info(f"  ✓ Tier 1: {turns} turns")
        return context

    async def get_tier2():
        if not classification["use_session_facts"]:
            return ""

        context = memory_router.session_memory.format_as_context(
            state["user_id"],
            state["conversation_id"],
            query=state["query"],
            limit=10
        )
        facts = memory_router.session_memory.search_facts(
            state["user_id"],
            state["conversation_id"],
            state["query"],
            limit=10
        )
        state["metadata"]["tier_2_facts"] = len(facts)
        state["metadata"]["tiers_used"].append("Tier 2 (Session)")

        logger.info(f"  ✓ Tier 2: {len(facts)} facts")
        return context

    async def get_tier3():
        if not classification["use_graphiti"]:
            return ""

        # Initialize backend
        backend = get_backend(
            state["backend_type"],
            **state.get("backend_config", {})
        )

        # Search Graphiti
        results = backend.search(
            state["query"],
            state["user_id"],
            limit=classification["search_limit"]
        )

        if results:
            context_parts = []
            for result in results:
                content = result.get("content", "")
                if content:
                    context_parts.append(content)

            context = "\n\n".join(context_parts)
            state["metadata"]["tier_3_memories"] = len(results)
            state["metadata"]["tiers_used"].append("Tier 3 (Graphiti)")

            logger.info(f"  ✓ Tier 3: {len(results)} memories")
            return context

        return ""

    # Execute all retrieval tasks in parallel
    tier1, tier2, tier3 = await asyncio.gather(
        get_tier1(),
        get_tier2(),
        get_tier3()
    )

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

    return state


def context_adapter_node(state: AgentState) -> AgentState:
    """
    Context Adapter Node - Optimize context based on model capabilities.

    GPT-4o: Full context (can handle 3K+ tokens)
    Local models (Qwen, Mistral): Compressed context (800 tokens max)
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

    if is_gpt4:
        # GPT-4o can handle full context
        state["optimized_context"] = combined_context
        logger.info(f"  GPT-4o: Using full context ({len(combined_context)} chars)")

    elif is_local:
        # Local models need compressed context
        # Simple compression: take first 3000 chars (roughly 800 tokens)
        max_chars = 3000

        if len(combined_context) > max_chars:
            # Prioritize recent context (Tier 1) over historical (Tier 3)
            tier1 = state["tier1_context"]
            tier2 = state["tier2_context"]
            tier3 = state["tier3_context"]

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

            logger.info(f"  Local model: Compressed context {len(combined_context)} → {len(state['optimized_context'])} chars")
        else:
            state["optimized_context"] = combined_context
            logger.info(f"  Local model: Context within limit ({len(combined_context)} chars)")

    else:
        # Other cloud models (Claude, etc) - use full context
        state["optimized_context"] = combined_context
        logger.info(f"  Cloud model: Using full context ({len(combined_context)} chars)")

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

    return state


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

def memory_route_langgraph(
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

    # Execute graph
    # Note: LangGraph's invoke handles async nodes automatically
    config = {"configurable": {"thread_id": conversation_id}}

    try:
        final_state = graph.invoke(initial_state, config=config)

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
