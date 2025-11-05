"""
Memory Router V2 - Enhanced with cache, backends, and profiles

New features:
- Conversational cache (80-90% hit rate)
- Pluggable backends (Graphiti, Supermemory)
- User profile context injection
- Better logging and diagnostics
- All previous features maintained
"""
import requests
import uuid
import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime

from modules.token_counter import (
    count_message_tokens,
    calculate_memory_tokens
)
from modules.conversation_cache import get_cache
from modules.profile_manager import get_profile_manager
from modules.backends import get_backend, MemoryBackend

logger = logging.getLogger(__name__)


def search_memories_with_cache(
    query: str,
    user_id: str,
    conversation_id: str,
    backend: MemoryBackend,
    limit: int = 5,
    cache_enabled: bool = True,
    model: str = "gpt-4o-mini"
) -> tuple[List[Dict], Dict]:
    """
    Search memories with intelligent caching.

    Args:
        query: Search query
        user_id: User identifier
        conversation_id: Conversation ID for cache
        backend: Memory backend to use
        limit: Max results
        cache_enabled: Enable cache
        model: Model for token counting

    Returns:
        Tuple of (memories, metadata with cache stats)
    """
    metadata = {
        "cache_hit": False,
        "cache_enabled": cache_enabled,
        "backend_type": backend.get_info()["type"]
    }

    # Try cache first
    if cache_enabled:
        cache = get_cache()
        cached_result = cache.get(conversation_id, query, model)

        if cached_result:
            memories, cache_metadata = cached_result
            metadata["cache_hit"] = True
            metadata["cache_age_seconds"] = cache_metadata.get("age_seconds", 0)

            logger.info(f"Cache HIT for conversation {conversation_id[:8]}...")
            return memories, metadata

        logger.info(f"Cache MISS for conversation {conversation_id[:8]}...")

    # Cache miss or disabled - search backend
    try:
        memories = backend.search(query, user_id, limit)
        metadata["memories_found"] = len(memories)

        # Store in cache
        if cache_enabled and memories:
            cache = get_cache()
            cache.set(conversation_id, query, memories, metadata, model)

        logger.info(f"Backend search returned {len(memories)} memories")
        return memories, metadata

    except Exception as e:
        logger.error(f"Memory search failed: {e}", exc_info=True)
        return [], {"error": str(e)}


def get_profile_context(
    user_id: str,
    profile_enabled: bool = True
) -> str:
    """
    Get user profile context if available.

    Args:
        user_id: User identifier
        profile_enabled: Enable profile injection

    Returns:
        Profile context string (empty if not found)
    """
    if not profile_enabled:
        return ""

    try:
        profile_manager = get_profile_manager()
        profile = profile_manager.get(user_id)

        if profile:
            context = profile.to_context()
            logger.info(f"Profile found for user {user_id}: {len(context)} chars")
            return context
        else:
            logger.debug(f"No profile found for user {user_id}")
            return ""

    except Exception as e:
        logger.error(f"Profile retrieval failed: {e}")
        return ""


def format_memories(memories: List[Dict]) -> str:
    """Format memories into context string."""
    if not memories:
        return ""

    formatted = []
    for idx, mem in enumerate(memories, 1):
        content = mem.get("content", "").strip()
        relevance = mem.get("relevance", 0)

        # Limit content length per memory
        if len(content) > 500:
            content = content[:497] + "..."

        formatted.append(f"{idx}. [{relevance:.2f}] {content}")

    context = "\n".join(formatted)

    return f"""
<relevant_context>
The following information from previous conversations may be relevant:

{context}
</relevant_context>
"""


def enrich_messages_with_context(
    messages: List[Dict],
    memory_context: str,
    profile_context: str
) -> List[Dict]:
    """
    Inject memory and profile context into messages.

    Args:
        messages: Original messages
        memory_context: Formatted memories
        profile_context: User profile
    Returns:
        Enriched messages
    """
    if not memory_context and not profile_context:
        return messages

    enriched = messages.copy()

    # Build combined context
    context_parts = []

    if profile_context:
        context_parts.append(f"<user_profile>\n{profile_context}\n</user_profile>")

    if memory_context:
        context_parts.append(memory_context)

    combined_context = "\n\n".join(context_parts)

    # Find existing system message
    system_idx = None
    for idx, msg in enumerate(enriched):
        if msg.get("role") == "system":
            system_idx = idx
            break

    if system_idx is not None:
        # Append to existing system message
        enriched[system_idx]["content"] += f"\n\n{combined_context}"
    else:
        # Insert new system message
        enriched.insert(0, {
            "role": "system",
            "content": f"You have access to the user's context and conversation history.\n\n{combined_context}"
        })

    return enriched


def store_memory_async(
    content: str,
    user_id: str,
    backend: MemoryBackend,
    metadata: Optional[Dict] = None
) -> int:
    """
    Store memory asynchronously using backend.

    Args:
        content: Memory content
        user_id: User identifier
        backend: Memory backend
        metadata: Optional metadata

    Returns:
        Number of chunks created
    """
    try:
        chunks_created = backend.store(content, user_id, metadata)
        logger.info(f"Stored memory: {chunks_created} chunks created")
        return chunks_created
    except Exception as e:
        logger.error(f"Memory storage failed: {e}")
        return 0


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


def memory_route(
    messages: List[Dict],
    model: str,
    user_id: str,
    provider_url: str,
    api_key: str,
    conversation_id: Optional[str] = None,
    backend_type: str = "graphiti",
    backend_config: Optional[Dict] = None,
    memory_enabled: bool = True,
    cache_enabled: bool = True,
    profile_enabled: bool = True,
    memory_search_limit: int = 5,
    memory_max_context_tokens: int = 2000,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False
) -> Dict:
    """
    Enhanced memory routing with cache, backends, and profiles.

    Args:
        messages: Chat messages
        model: LLM model
        user_id: User identifier
        provider_url: LLM provider URL
        api_key: Provider API key
        conversation_id: Conversation ID (auto-generated if None)
        backend_type: Memory backend ("graphiti" or "supermemory")
        backend_config: Backend configuration
        memory_enabled: Enable memory features
        cache_enabled: Enable conversational cache
        profile_enabled: Enable profile context
        memory_search_limit: Max memories to retrieve
        memory_max_context_tokens: Max tokens for memory context
        temperature: Sampling temperature
        max_tokens: Max response tokens
        stream: Stream response

    Returns:
        LLM response with enhanced metadata
    """
    start_time = datetime.now()

    # Generate conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # Initialize metadata
    metadata = {
        "conversation_id": conversation_id,
        "backend_type": backend_type,
        "cache_enabled": cache_enabled,
        "profile_enabled": profile_enabled,
        "cache_hit": False,
        "profile_found": False,
        "chunks_retrieved": 0,
        "chunks_created": 0,
        "context_modified": False,
        "tokens_input": 0,
        "tokens_output": 0,
        "tokens_memory": 0,
        "tokens_profile": 0,
        "tokens_processed": 0,
        "processing_time_ms": 0,
        "error": None
    }

    try:
        # Initialize backend
        backend_config = backend_config or {}
        backend = get_backend(backend_type, **backend_config)

        # Count tokens in original messages
        original_tokens = count_message_tokens(messages, model)
        metadata["tokens_input"] = original_tokens

        # Extract user's last message
        user_messages = [m for m in messages if m.get("role") == "user"]
        query = user_messages[-1]["content"] if user_messages else ""

        # Get profile context
        profile_context = ""
        if profile_enabled:
            profile_context = get_profile_context(user_id, profile_enabled)
            if profile_context:
                metadata["profile_found"] = True
                metadata["tokens_profile"] = len(profile_context.split())  # Approximate

        # Search memories (with cache)
        memories = []
        if memory_enabled and query:
            memories, search_metadata = search_memories_with_cache(
                query=query,
                user_id=user_id,
                conversation_id=conversation_id,
                backend=backend,
                limit=memory_search_limit,
                cache_enabled=cache_enabled,
                model=model
            )

            metadata.update(search_metadata)
            metadata["chunks_retrieved"] = len(memories)

            if memories:
                metadata["tokens_memory"] = calculate_memory_tokens(memories, model)

        # Format memories
        memory_context = format_memories(memories) if memories else ""

        # Enrich messages
        enriched_messages = enrich_messages_with_context(
            messages, memory_context, profile_context
        )

        metadata["context_modified"] = bool(memory_context or profile_context)

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
            metadata["tokens_processed"] = usage.get("total_tokens", 0)

        # Store new memory asynchronously
        # For Graphiti: Queues episode for processing with full entity extraction
        # Processing happens in background queue, preserving all knowledge graph features
        if not stream and memory_enabled and query:
            assistant_response = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Truncate very long responses to prevent token limit issues in entity extraction
            # Graphiti context can grow large, so we limit episode content to ~1000 chars
            max_content_length = 1000
            if len(assistant_response) > max_content_length:
                assistant_response = assistant_response[:max_content_length] + "... [truncated]"
            
            memory_content = f"User: {query}\nAssistant: {assistant_response}"

            # Fire-and-forget storage (backend uses queue for async processing)
            def store_in_background():
                try:
                    chunks = store_memory_async(
                        memory_content,
                        user_id,
                        backend,
                        metadata={
                            "timestamp": datetime.now().isoformat(),
                            "model": model,
                            "conversation_id": conversation_id
                        }
                    )
                    logger.info(f"Storage queued: {chunks} chunks (processing in background)")
                except Exception as e:
                    logger.error(f"Background storage queue failed: {e}")
            
            # Start background thread to queue storage (returns immediately)
            storage_thread = threading.Thread(target=store_in_background, daemon=True)
            storage_thread.start()
            metadata["chunks_created"] = 0  # Processing happens async in queue

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
