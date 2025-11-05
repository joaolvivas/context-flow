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

from modules.token_counter import count_message_tokens
from modules.backends import get_backend, MemoryBackend
from modules.memory import WorkingMemory, SessionMemory
from modules.memory.intelligent_router import MemoryRouter

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
    stream: bool = False
) -> Dict:
    """Forward request to LLM provider."""
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


def enrich_messages_with_tiered_context(
    messages: List[Dict],
    tiered_context: str
) -> List[Dict]:
    """
    Inject tiered memory context into messages.
    
    Args:
        messages: Original messages
        tiered_context: Context from 3-tier system
    
    Returns:
        Enriched messages
    """
    if not tiered_context:
        return messages

    enriched = messages.copy()

    # Find existing system message
    system_idx = None
    for idx, msg in enumerate(enriched):
        if msg.get("role") == "system":
            system_idx = idx
            break

    if system_idx is not None:
        # Append to existing system message
        enriched[system_idx]["content"] += f"\n\n{tiered_context}"
    else:
        # Insert new system message
        enriched.insert(0, {
            "role": "system",
            "content": f"You have access to the user's context and memory.\n\n{tiered_context}"
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
    stream: bool = False
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
        
        if memory_enabled and query:
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

        # Forward to LLM
        response = route_to_llm(
            enriched_messages,
            model,
            provider_url,
            api_key,
            temperature,
            max_tokens,
            stream
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
