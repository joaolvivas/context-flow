"""
Memory Router V3 - 3-Tier Memory Architecture

Revolutionary multi-tier memory system:
- Tier 1 (Working Memory): Recent conversation in Redis (instant, zero cost)
- Tier 2 (Session Memory): Extracted facts in Redis (fast, low cost)
- Tier 3 (Long-term): Graphiti + Neo4j (deep, higher cost, only when needed)

Performance: 90% of queries <100ms, 50-80% token savings
"""
import os
import requests
import uuid
import logging
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from modules.token_counter import count_message_tokens
from modules.backends import get_backend, MemoryBackend
from modules.memory import WorkingMemory, SessionMemory
from modules.memory.intelligent_router import MemoryRouter
from modules.conversation_cache import get_cache

logger = logging.getLogger(__name__)

# Global memory system instances
_working_memory = None
_session_memory = None
_memory_router = None


def get_memory_system() -> MemoryRouter:
    """
    Get or initialize the 3-tier memory system.
    
    Returns:
        MemoryRouter instance
    """
    global _working_memory, _session_memory, _memory_router
    
    if _memory_router is None:
        # Initialize Tier 1: Working Memory
        _working_memory = WorkingMemory(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=0,
            max_turns=int(os.getenv("WORKING_MEMORY_TURNS", "20")),
            ttl_seconds=int(os.getenv("WORKING_MEMORY_TTL", "1800"))  # 30 min
        )
        
        # Initialize Tier 2: Session Memory
        _session_memory = SessionMemory(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=1,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("SESSION_MEMORY_MODEL", "gpt-4o-mini"),
            ttl_seconds=int(os.getenv("SESSION_MEMORY_TTL", "86400"))  # 24 hours
        )
        
        # Initialize router
        _memory_router = MemoryRouter(
            working_memory=_working_memory,
            session_memory=_session_memory,
            graphiti_enabled=os.getenv("GRAPHITI_ENABLED", "true").lower() == "true"
        )
        
        logger.info("3-Tier memory system initialized")
        logger.info(f"  Tier 1 (Working): {_working_memory.max_turns} turns, {_working_memory.ttl_seconds}s TTL")
        logger.info(f"  Tier 2 (Session): Model {_session_memory.model}, {_session_memory.ttl_seconds}s TTL")
        logger.info(f"  Tier 3 (Graphiti): {'Enabled' if _memory_router.graphiti_enabled else 'Disabled'}")
    
    return _memory_router


def route_to_llm(
    messages: List[Dict],
    model: str,
    provider_url: str,
    api_key: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    tools: Optional[List[Dict]] = None,
    tool_choice: Optional[Dict] = None,
    functions: Optional[List[Dict]] = None,
    function_call: Optional[Dict] = None,
    **extra_params
) -> Dict:
    """
    Forward request to LLM provider.

    Supports dual routing:
    - Real API key → Forward to remote provider (OpenAI, Claude, etc.)
    - "local-dev" or empty → Route to local MLX model at localhost:11964

    Passes through all OpenAI parameters including tools/functions for MCP compatibility.
    """
    # Detect local model routing
    is_local = api_key in ["local-dev", "", None]

    if is_local:
        # Route to local MLX endpoint
        provider_url = "http://localhost:11964/v1"
        model = "mistral:latest"
        api_key = "local-dev"
        logger.info(f"Routing to LOCAL MLX model at {provider_url}")
    else:
        logger.info(f"Routing to REMOTE provider: {provider_url}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": stream
    }

    if max_tokens:
        payload["max_tokens"] = max_tokens

    # Forward tool calling parameters (newer format - MCP uses this)
    if tools:
        payload["tools"] = tools
    if tool_choice:
        payload["tool_choice"] = tool_choice

    # Forward function calling parameters (legacy format)
    if functions:
        payload["functions"] = functions
    if function_call:
        payload["function_call"] = function_call

    # Forward any additional parameters
    payload.update(extra_params)

    response = requests.post(
        f"{provider_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
        stream=stream
    )

    response.raise_for_status()

    if stream:
        return response
    else:
        return response.json()


def get_memory_system_prompt() -> str:
    """
    Concise system prompt explaining memory capabilities.
    
    Optimized from 86 lines to 30 lines, saving ~400 tokens per request.
    """
    return """You have automatic access to personalized context from 3 memory tiers:

**Working Memory**: Last 10 conversation turns (always included)
**Session Facts**: Key information from past conversations  
**Knowledge Graph**: Deep historical context with entity relationships and professional background

**Context Format:**
- Node summaries (rich biographical info): [Entity: Name] detailed description...
- Specific facts: Individual statements and relationships

**CRITICAL Instructions:**

1. **Trust and use provided context confidently** - Never claim ignorance when information is below

2. **Use memories naturally** - Don't say "based on provided context" - just use it as if you remember

3. **For comprehensive queries** ("tell me everything", "quem sou eu?"):
   - Organize by category (goals, background, experience, projects, skills)
   - Prioritize node summaries for biographical details
   - Be specific with achievements and metrics
   - Provide complete, professional summary

4. **Acknowledge gaps honestly** - If specific info ISN'T in context, say so

**Your Memory Context:**

---"""


def enrich_messages_with_tiered_context(
    messages: List[Dict],
    tiered_context: str
) -> List[Dict]:
    """
    Inject tiered memory context into messages with intelligent system prompt.

    Args:
        messages: Original messages
        tiered_context: Context from 3-tier system

    Returns:
        Enriched messages with system prompt + memory context
    """
    if not tiered_context:
        return messages

    enriched = messages.copy()

    # Get intelligent system prompt
    system_prompt = get_memory_system_prompt()

    # Combine system prompt with actual memory context
    full_system_content = f"{system_prompt}\n\n## Your Memory Context:\n\n{tiered_context}"

    # Find existing system message
    system_idx = None
    for idx, msg in enumerate(enriched):
        if msg.get("role") == "system":
            system_idx = idx
            break

    if system_idx is not None:
        # Preserve user's original system message, append our memory system prompt
        original_content = enriched[system_idx]["content"]
        enriched[system_idx]["content"] = f"{original_content}\n\n{full_system_content}"
    else:
        # Insert new system message with memory awareness
        enriched.insert(0, {
            "role": "system",
            "content": full_system_content
        })

    return enriched


def memory_route_v3(
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
    **extra_params
) -> Dict:
    """
    3-Tier memory routing with intelligent tier selection.

    Flow:
    1. Extract user query
    2. Get context from appropriate tiers (Working + Session + Graphiti when needed)
    3. Enrich messages with context
    4. Forward to LLM
    5. Store response across tiers

    Args:
        messages: Chat messages
        model: LLM model
        user_id: User identifier
        provider_url: LLM provider URL
        api_key: Provider API key
        conversation_id: Conversation ID (auto-generated if None)
        backend_type: Memory backend for Tier 3 ("graphiti" or "supermemory")
        backend_config: Backend configuration
        memory_enabled: Enable memory features
        temperature: Sampling temperature
        max_tokens: Max response tokens
        stream: Stream response
        tools: Tool definitions for function calling (MCP format)
        tool_choice: Tool selection strategy
        functions: Function definitions (legacy format)
        function_call: Function calling strategy (legacy format)
        **extra_params: Additional parameters to pass to LLM

    Returns:
        LLM response with memory metadata
    """
    start_time = datetime.now()

    # Generate conversation ID if not provided
    # Use user_id as stable conversation ID so memories persist across requests
    if not conversation_id:
        conversation_id = f"default-{user_id}"

    # Initialize metadata
    metadata = {
        "conversation_id": conversation_id,
        "memory_enabled": memory_enabled,
        "tiers_used": [],
        "tier_1_turns": 0,
        "tier_2_facts": 0,
        "tier_3_memories": 0,
        "tier_1_cost": 0,
        "tier_2_cost": 0,
        "tier_3_cost": 0,
        "total_cost_estimate": 0,
        "tokens_input": 0,
        "tokens_output": 0,
        "tokens_memory": 0,
        "processing_time_ms": 0,
        "error": None
    }

    try:
        # Count tokens in original messages
        original_tokens = count_message_tokens(messages, model)
        metadata["tokens_input"] = original_tokens

        # Extract user's last message
        user_messages = [m for m in messages if m.get("role") == "user"]
        query = user_messages[-1]["content"] if user_messages else ""

        # Initialize memory system
        memory_router = get_memory_system()
        
        # Get tiered memory context
        tiered_context = ""
        memory_metadata = {}
        cache_hit = False
        
        if memory_enabled and query:
            # Initialize cache
            cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
            if cache_enabled:
                cache = get_cache(
                    max_size=int(os.getenv("CACHE_MAX_SIZE", "100")),
                    ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "900")),
                    similarity_threshold=float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.85"))
                )
                
                # Check cache first
                cached_result = cache.get(conversation_id, query, model)
                if cached_result:
                    tiered_context, memory_metadata = cached_result
                    cache_hit = True
                    logger.info(f"✓ Cache HIT for conversation {conversation_id}")
                    metadata["cache_hit"] = True
            
            # Cache miss - retrieve from tiers
            if not cache_hit:
                # Initialize Tier 3 backend (for deep queries)
                backend_config = backend_config or {}
                backend = get_backend(backend_type, **backend_config)
                
                # Define Graphiti search function
                def graphiti_search(q, uid, limit=3):
                    return backend.search(q, uid, limit)
                
                # Get context from appropriate tiers
                tiered_context, memory_metadata = memory_router.get_memory_context(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    query=query,
                    graphiti_search_func=graphiti_search if memory_router.graphiti_enabled else None
                )
                
                # Store in cache for future queries
                if cache_enabled and tiered_context:
                    cache.set(conversation_id, query, tiered_context, memory_metadata, model)
                    logger.info(f"✓ Stored in cache for conversation {conversation_id}")
                
                metadata["cache_hit"] = False
            
            # Update metadata from tier usage
            metadata["tiers_used"] = memory_metadata.get("tiers_used", [])
            metadata["tier_1_turns"] = memory_metadata.get("working_memory_turns", 0)
            metadata["tier_2_facts"] = memory_metadata.get("session_facts", 0)
            metadata["tier_3_memories"] = memory_metadata.get("graphiti_memories", 0)
            metadata["total_cost_estimate"] = memory_metadata.get("total_cost_estimate", 0)
            
            # Log tier usage
            logger.info(f"Memory tiers used: {metadata['tiers_used']}")
            logger.info(f"Cost estimate: {metadata['total_cost_estimate']} tokens")

        # Enrich messages with tiered context
        enriched_messages = enrich_messages_with_tiered_context(messages, tiered_context)
        
        # Count memory tokens
        if tiered_context:
            metadata["tokens_memory"] = len(tiered_context.split())  # Approximate

        # Forward to LLM (pass through all parameters including tools for MCP)
        response = route_to_llm(
            enriched_messages,
            model,
            provider_url,
            api_key,
            temperature,
            max_tokens,
            stream,
            tools=tools,
            tool_choice=tool_choice,
            functions=functions,
            function_call=function_call,
            **extra_params
        )

        # Extract token usage
        if not stream:
            usage = response.get("usage", {})
            metadata["tokens_output"] = usage.get("completion_tokens", 0)

        # Store response across tiers (async)
        if not stream and memory_enabled and query:
            assistant_response = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Truncate very long responses to prevent token limit issues
            max_content_length = 1000
            if len(assistant_response) > max_content_length:
                assistant_response = assistant_response[:max_content_length] + "... [truncated]"
            
            # Capture backend variables for closure
            _backend = backend
            _backend_type = backend_type
            _backend_config = backend_config or {}
            
            # Store in background thread
            def store_in_background():
                try:
                    # Store across Tier 1 and Tier 2
                    storage_meta = memory_router.store_conversation_turn(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        user_message=query,
                        assistant_response=assistant_response,
                        extract_facts=True  # Enable Tier 2 fact extraction
                    )
                    
                    logger.info(f"Tier 1 stored: {storage_meta['working_memory_stored']}")
                    logger.info(f"Tier 2 facts: {storage_meta['session_facts_extracted']}")
                    
                    # Store in Tier 3 (Graphiti) - queued
                    memory_content = f"User: {query}\nAssistant: {assistant_response}"
                    
                    chunks = _backend.store(
                        memory_content,
                        user_id,
                        metadata={
                            "timestamp": datetime.now().isoformat(),
                            "model": model,
                            "conversation_id": conversation_id
                        }
                    )
                    logger.info(f"Tier 3 queued: {chunks} chunks")
                    
                except Exception as e:
                    logger.error(f"Background storage error: {e}")
            
            # Start background thread
            storage_thread = threading.Thread(target=store_in_background, daemon=True)
            storage_thread.start()

    except Exception as e:
        logger.error(f"Memory routing error: {e}", exc_info=True)
        metadata["error"] = str(e)

        # Fallback without memory
        if "response" not in locals():
            enriched_messages = messages
            response = route_to_llm(
                enriched_messages,
                model,
                provider_url,
                api_key,
                temperature,
                max_tokens,
                stream
            )

    # Calculate processing time
    metadata["processing_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000

    # Add metadata to response
    if not stream:
        response["_memory_metadata"] = metadata

    return response
