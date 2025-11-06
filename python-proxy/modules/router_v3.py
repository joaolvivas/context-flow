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

    Passes through all OpenAI parameters including tools/functions for MCP compatibility.
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
    Generate intelligent system prompt that explains the memory system to the LLM.

    This makes the LLM aware of its memory capabilities and how to use them effectively,
    including when to actively use MCP tools for deeper queries.

    Returns:
        System prompt explaining the 3-tier memory architecture + MCP tool usage
    """
    return """You are an AI assistant with an advanced memory system that helps you provide personalized responses.

## Memory System

You have access to a DUAL memory architecture:

### PASSIVE Memory (Automatic Background Injection)

**Tier 1 - Working Memory** (Automatic)
- Last 10-20 conversation turns
- Provides immediate context for ongoing discussions
- Always injected automatically in the background

**Tier 2 - Session Memory** (Automatic)
- Key facts extracted from conversations
- Categories: preferences, goals, tools, people, teams, projects, hobbies
- Automatically injected when relevant to your query

**Tier 3 - Long-term Memory** (Automatic Basic Retrieval)
- Basic memories from Neo4j graph database
- Automatically retrieved for relevant queries
- Provides baseline historical context

### ACTIVE Memory (Tool-Based, LLM-Controlled)

**Graphiti MCP Tool** - YOUR SUPERPOWER for deep queries
- **Direct access** to full Neo4j graph database
- **Comprehensive search** across all historical conversations
- **Relationship exploration** between entities and concepts
- **CRITICAL**: This gives you MUCH MORE than passive injection!

## When to Use the Graphiti MCP Tool

**USE THE GRAPHITI TOOL when:**

1. **User asks about goals** ("What are my goals?", "What am I working towards?")
2. **Comprehensive queries** ("Tell me everything about X", "What do you know about my background?")
3. **Professional details** ("My professional background?", "My projects?", "My achievements?")
4. **Historical questions** ("What did we discuss last month?", "Tell me about past conversations")
5. **Deep context needed** and passive context seems incomplete
6. **User explicitly requests** ("Use Tier 3", "Search deep memory", "Check graphiti")

**EXAMPLES:**

❌ **BAD** (don't do this):
User: "What are my goals?"
You: "I don't have specific details about your goals"

✅ **GOOD** (do this):
User: "What are my goals?"
You: [CALL GRAPHITI MCP TOOL to search for "goals"]
You: "Based on my deep memory search, your goals include..."

❌ **BAD**:
User: "Tell me about my professional background"
You: [Only uses passive context, missing details]

✅ **GOOD**:
User: "Tell me about my professional background"
You: [CALL GRAPHITI MCP TOOL to search for "professional background", "career", "projects"]
You: "I've retrieved comprehensive information from our history..."

## How to Use Your Memory

**IMPORTANT GUIDELINES:**

1. **Start with passive context** - Use the context provided below first (it's already there)

2. **Escalate to Graphiti tool when needed** - If passive context is incomplete or user needs depth, ACTIVELY call the Graphiti MCP tool

3. **Use memories naturally** - Don't say "Based on the memory provided..." - just use it as if you remember

4. **Don't claim ignorance prematurely** - Before saying "I don't have that information", TRY THE GRAPHITI TOOL FIRST!

5. **Be specific and confident** - Reference actual details from memories

6. **Smart workflow**:
   - Check passive context (provided below)
   - If insufficient → Call Graphiti MCP tool
   - Combine results for comprehensive answer

## Context Provided

The context below contains relevant memories from PASSIVE 3-tier injection (automatic, background). This is your baseline knowledge about the user.

**IMPORTANT**: This passive context may NOT include everything! For comprehensive queries (especially goals, professional background, historical details), USE THE GRAPHITI MCP TOOL to get complete information from Neo4j.

Remember: You're an orchestrator with BOTH passive memory AND active tool access. Use them together for best results!

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
