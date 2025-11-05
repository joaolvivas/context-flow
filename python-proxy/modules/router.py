"""
Memory Router - Transparent proxy for LLM with automatic memory management

Inspired by Supermemory's Memory Router:
- Intercepts LLM requests
- Searches for relevant memories
- Enriches context automatically
- Stores new memories asynchronously
- Falls back gracefully on errors
"""
import requests
from typing import Dict, List, Optional
from datetime import datetime


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

        # Limit content length
        if len(content) > 200:
            content = content[:197] + "..."

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
    metadata: Optional[Dict] = None
) -> None:
    """
    Store new memory asynchronously (fire-and-forget).

    This should be called AFTER sending response to user,
    to avoid blocking the response.

    Args:
        content: Memory content to store
        user_id: User identifier
        mcp_endpoint: MCP storage endpoint
        metadata: Optional metadata (timestamp, etc)
    """
    try:
        # Non-blocking request with short timeout
        requests.post(
            mcp_endpoint,
            json={
                "content": content,
                "user_id": user_id,
                "metadata": metadata or {}
            },
            timeout=0.5  # Don't wait for response
        )
    except:
        # Fire-and-forget - ignore errors
        pass


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
    mcp_search_endpoint: str = "http://localhost:5000/mcp/search",
    mcp_store_endpoint: str = "http://localhost:5000/mcp/store",
    memory_enabled: bool = True,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False
) -> Dict:
    """
    Main routing function - the Memory Router.

    Flow:
    1. Extract user's last message as search query
    2. Search for relevant memories (if enabled)
    3. Enrich messages with memory context
    4. Forward to LLM provider
    5. Store new memory asynchronously
    6. Return response

    This mimics Supermemory's Memory Router behavior.

    Args:
        messages: Chat messages array
        model: LLM model to use
        user_id: User identifier for memory namespace
        provider_url: LLM provider base URL (e.g., 'https://api.openai.com/v1')
        api_key: LLM provider API key
        mcp_search_endpoint: MCP search endpoint
        mcp_store_endpoint: MCP store endpoint
        memory_enabled: Whether to use memory features
        temperature: Sampling temperature
        max_tokens: Max response tokens
        stream: Whether to stream response

    Returns:
        LLM response with added headers:
        - x-memory-chunks-retrieved
        - x-memory-modified
        - x-memory-tokens-processed (approximate)
    """
    start_time = datetime.now()

    # Extract user's last message for search query
    user_messages = [m for m in messages if m.get("role") == "user"]
    query = user_messages[-1]["content"] if user_messages else ""

    # Search memories
    memories = []
    if memory_enabled and query:
        memories = search_memories(query, user_id, mcp_search_endpoint)

    # Enrich messages with memories
    enriched_messages = enrich_messages(messages, memories)
    context_modified = len(memories) > 0

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

    # Store new memory asynchronously (if not streaming)
    if not stream and memory_enabled and query:
        # Extract assistant response
        assistant_response = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Combine user message + assistant response as memory
        memory_content = f"User: {query}\nAssistant: {assistant_response}"

        # Fire-and-forget storage
        store_memory_async(
            memory_content,
            user_id,
            mcp_store_endpoint,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "model": model
            }
        )

    # Add diagnostic headers (in metadata)
    if not stream:
        response["_memory_metadata"] = {
            "chunks_retrieved": len(memories),
            "context_modified": context_modified,
            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
        }

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
