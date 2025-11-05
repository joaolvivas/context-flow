"""
Memory Router - Transparent proxy for LLM with automatic memory management

Inspired by Supermemory's Memory Router:
- Intercepts LLM requests
- Searches for relevant memories
- Enriches context automatically
- Stores new memories asynchronously
- Falls back gracefully on errors
- Intelligent chunking for long messages
- Token counting and optimization
- Conversation tracking
"""
import requests
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from modules.token_counter import (
    count_message_tokens,
    count_tokens,
    calculate_memory_tokens,
    get_context_window_size
)
from modules.chunking import chunk_text, chunk_conversation, should_chunk


def search_memories(
    query: str,
    user_id: str,
    mcp_endpoint: str = "http://localhost:5000/mcp/search",
    limit: int = 5,
    timeout: float = 1.5
) -> List[Dict]:
    """
    Search for relevant memories via MCP/Graphiti.

    Args:
        query: Search query (usually the user's message)
        user_id: User identifier (namespace for memories)
        mcp_endpoint: MCP server URL
        limit: Max number of memories to retrieve
        timeout: Request timeout in seconds

    Returns:
        List of memory objects with 'content', 'relevance', etc.
        Returns empty list on error (graceful degradation)
    """
    try:
        response = requests.post(
            mcp_endpoint,
            json={
                "query": query,
                "user_id": user_id,
                "limit": limit
            },
            timeout=timeout
        )

        if response.status_code != 200:
            return []

        data = response.json()
        return data.get("results", [])

    except (requests.Timeout, requests.ConnectionError):
        # Graceful degradation - continue without memories
        return []
    except Exception:
        return []


def prioritize_memories(
    memories: List[Dict],
    max_tokens: int,
    model: str = "gpt-4o-mini"
) -> List[Dict]:
    """
    Prioritize and filter memories to fit within token budget.

    Strategy:
    - Sort by relevance (highest first)
    - Keep adding memories until token limit reached
    - Always keep at least top 2 memories if possible

    Args:
        memories: List of memory objects with 'relevance' scores
        max_tokens: Maximum tokens for memory context
        model: Model name for token counting

    Returns:
        Filtered list of memories
    """
    if not memories:
        return []

    # Sort by relevance (highest first)
    sorted_memories = sorted(
        memories,
        key=lambda m: m.get("relevance", 0),
        reverse=True
    )

    # Track token usage
    current_tokens = 0
    selected_memories = []

    for mem in sorted_memories:
        content = mem.get("content", "")
        mem_tokens = count_tokens(content, model)

        # Check if we can fit this memory
        if current_tokens + mem_tokens <= max_tokens:
            selected_memories.append(mem)
            current_tokens += mem_tokens
        elif len(selected_memories) < 2:
            # Always keep at least 2 memories even if slightly over budget
            selected_memories.append(mem)
            current_tokens += mem_tokens
        else:
            # Budget exhausted
            break

    return selected_memories


def format_memories(memories: List[Dict]) -> str:
    """
    Format memories into context string for LLM.

    Args:
        memories: List of memory objects

    Returns:
        Formatted string to inject into prompt, or empty string
    """
    if not memories:
        return ""

    formatted = []
    for idx, mem in enumerate(memories, 1):
        content = mem.get("content", "").strip()
        relevance = mem.get("relevance", 0)

        # Limit content length per memory (not total)
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


def enrich_messages(
    messages: List[Dict],
    memories: List[Dict]
) -> List[Dict]:
    """
    Inject memory context into messages array.

    Strategy: Add context as system message at the beginning,
    or append to existing system message.

    Args:
        messages: Original messages array
        memories: Retrieved memories

    Returns:
        Enriched messages array
    """
    if not memories:
        return messages

    context = format_memories(memories)
    enriched = messages.copy()

    # Find existing system message
    system_idx = None
    for idx, msg in enumerate(enriched):
        if msg.get("role") == "system":
            system_idx = idx
            break

    if system_idx is not None:
        # Append to existing system message
        enriched[system_idx]["content"] += context
    else:
        # Insert new system message at start
        enriched.insert(0, {
            "role": "system",
            "content": f"You have access to the user's conversation history.{context}"
        })

    return enriched


def store_memory_async(
    content: str,
    user_id: str,
    mcp_endpoint: str = "http://localhost:5000/mcp/store",
    metadata: Optional[Dict] = None,
    model: str = "gpt-4o-mini",
    chunk_size: int = 500
) -> int:
    """
    Store new memory asynchronously (fire-and-forget) with intelligent chunking.

    This should be called AFTER sending response to user,
    to avoid blocking the response.

    Args:
        content: Memory content to store
        user_id: User identifier
        mcp_endpoint: MCP storage endpoint
        metadata: Optional metadata (timestamp, conversation_id, etc)
        model: Model name for token counting
        chunk_size: Max tokens per chunk

    Returns:
        Number of chunks created
    """
    chunks_created = 0

    try:
        # Check if content needs chunking
        if should_chunk(content, model, chunk_size):
            # Split into semantic chunks
            chunks = chunk_text(content, model, chunk_size)

            # Store each chunk separately
            for chunk in chunks:
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    "chunk_index": chunk["index"],
                    "total_chunks": len(chunks),
                    "chunk_tokens": chunk["tokens"]
                })

                requests.post(
                    mcp_endpoint,
                    json={
                        "content": chunk["content"],
                        "user_id": user_id,
                        "metadata": chunk_metadata
                    },
                    timeout=0.5
                )
                chunks_created += 1
        else:
            # Store as single memory
            requests.post(
                mcp_endpoint,
                json={
                    "content": content,
                    "user_id": user_id,
                    "metadata": metadata or {}
                },
                timeout=0.5
            )
            chunks_created = 1

    except:
        # Fire-and-forget - ignore errors
        pass

    return chunks_created


def route_to_llm(
    messages: List[Dict],
    model: str,
    provider_url: str,
    api_key: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False
) -> Dict:
    """
    Forward request to actual LLM provider.

    Args:
        messages: Messages array (potentially enriched)
        model: Model name
        provider_url: LLM provider base URL
        api_key: Provider API key
        temperature: Sampling temperature
        max_tokens: Max response tokens
        stream: Whether to stream response

    Returns:
        LLM response in OpenAI format
    """
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
        return response  # Return raw response for streaming
    else:
        return response.json()


def memory_route(
    messages: List[Dict],
    model: str,
    user_id: str,
    provider_url: str,
    api_key: str,
    conversation_id: Optional[str] = None,
    mcp_search_endpoint: str = "http://localhost:5000/mcp/search",
    mcp_store_endpoint: str = "http://localhost:5000/mcp/store",
    memory_enabled: bool = True,
    memory_max_context_tokens: int = 2000,
    memory_chunk_size: int = 500,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False
) -> Dict:
    """
    Main routing function - the Memory Router (Enhanced).

    Flow:
    1. Generate/validate conversation_id
    2. Count tokens in original messages
    3. Extract user's last message as search query
    4. Search for relevant memories (if enabled)
    5. Prioritize memories based on token budget
    6. Enrich messages with memory context
    7. Count tokens in enriched messages
    8. Forward to LLM provider
    9. Store new memory asynchronously with chunking
    10. Return response with diagnostic metadata

    This mimics and enhances Supermemory's Memory Router behavior.

    Args:
        messages: Chat messages array
        model: LLM model to use
        user_id: User identifier for memory namespace
        provider_url: LLM provider base URL (e.g., 'https://api.openai.com/v1')
        api_key: LLM provider API key
        conversation_id: Conversation ID (auto-generated if not provided)
        mcp_search_endpoint: MCP search endpoint
        mcp_store_endpoint: MCP store endpoint
        memory_enabled: Whether to use memory features
        memory_max_context_tokens: Max tokens for memory context
        memory_chunk_size: Chunk size for storing memories
        temperature: Sampling temperature
        max_tokens: Max response tokens
        stream: Whether to stream response

    Returns:
        LLM response with added metadata:
        - x-memory-conversation-id
        - x-memory-chunks-retrieved
        - x-memory-chunks-created
        - x-memory-context-modified
        - x-memory-tokens-input
        - x-memory-tokens-output
        - x-memory-tokens-memory
        - x-memory-tokens-processed
        - x-memory-processing-time-ms
        - x-memory-error (if error occurred)
    """
    start_time = datetime.now()

    # Generate conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # Initialize metadata
    metadata = {
        "conversation_id": conversation_id,
        "chunks_retrieved": 0,
        "chunks_created": 0,
        "context_modified": False,
        "tokens_input": 0,
        "tokens_output": 0,
        "tokens_memory": 0,
        "tokens_processed": 0,
        "processing_time_ms": 0,
        "error": None
    }

    try:
        # Count tokens in original messages
        original_tokens = count_message_tokens(messages, model)
        metadata["tokens_input"] = original_tokens

        # Extract user's last message for search query
        user_messages = [m for m in messages if m.get("role") == "user"]
        query = user_messages[-1]["content"] if user_messages else ""

        # Search memories
        memories = []
        if memory_enabled and query:
            memories = search_memories(query, user_id, mcp_search_endpoint)

            # Prioritize memories to fit token budget
            if memories:
                memories = prioritize_memories(
                    memories,
                    max_tokens=memory_max_context_tokens,
                    model=model
                )

        metadata["chunks_retrieved"] = len(memories)

        # Calculate memory token usage
        if memories:
            metadata["tokens_memory"] = calculate_memory_tokens(memories, model)

        # Enrich messages with memories
        enriched_messages = enrich_messages(messages, memories)
        context_modified = len(memories) > 0
        metadata["context_modified"] = context_modified

        # Count tokens in enriched messages
        enriched_tokens = count_message_tokens(enriched_messages, model)

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

        # Extract token usage from LLM response
        if not stream:
            usage = response.get("usage", {})
            metadata["tokens_output"] = usage.get("completion_tokens", 0)
            metadata["tokens_processed"] = usage.get("total_tokens", enriched_tokens + metadata["tokens_output"])

        # Store new memory asynchronously (if not streaming)
        if not stream and memory_enabled and query:
            # Extract assistant response
            assistant_response = response.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Combine user message + assistant response as memory
            memory_content = f"User: {query}\nAssistant: {assistant_response}"

            # Fire-and-forget storage with chunking
            chunks_created = store_memory_async(
                memory_content,
                user_id,
                mcp_store_endpoint,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "model": model,
                    "conversation_id": conversation_id
                },
                model=model,
                chunk_size=memory_chunk_size
            )
            metadata["chunks_created"] = chunks_created

    except Exception as e:
        # Track error but don't fail the request
        metadata["error"] = str(e)

        # If we haven't called LLM yet, do fallback without memory
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

    # Calculate total processing time
    metadata["processing_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000

    # Add diagnostic metadata (in special field)
    if not stream:
        response["_memory_metadata"] = metadata

    return response


# Convenience function for simple usage
def route(
    prompt: str,
    user_id: str,
    model: str = "gpt-4o-mini",
    provider_url: str = "https://api.openai.com/v1",
    api_key: str = "",
    memory_enabled: bool = True
) -> str:
    """
    Simple convenience function for single-turn conversations.

    Args:
        prompt: User's message
        user_id: User identifier
        model: LLM model
        provider_url: Provider base URL
        api_key: Provider API key
        memory_enabled: Use memory features

    Returns:
        Assistant's response text
    """
    messages = [{"role": "user", "content": prompt}]

    response = memory_route(
        messages=messages,
        model=model,
        user_id=user_id,
        provider_url=provider_url,
        api_key=api_key,
        memory_enabled=memory_enabled,
        stream=False
    )

    return response["choices"][0]["message"]["content"]
