"""
Token counting utilities using tiktoken

Provides accurate token counting for different models and formats.
Used for diagnostics, cost tracking, and context window management.
"""
import tiktoken
from typing import List, Dict, Optional


# Model to encoding mapping (tiktoken)
MODEL_ENCODINGS = {
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "claude": "cl100k_base",  # Approximation for Claude
    "gemini": "cl100k_base",  # Approximation for Gemini
}


def get_encoding_for_model(model: str) -> str:
    """
    Get the appropriate tiktoken encoding for a model.

    Args:
        model: Model name (e.g., "gpt-4o-mini")

    Returns:
        Encoding name (e.g., "o200k_base")
    """
    # Try exact match
    if model in MODEL_ENCODINGS:
        return MODEL_ENCODINGS[model]

    # Try prefix match (e.g., "gpt-4o-mini-2024-07-18" -> "gpt-4o")
    for model_prefix, encoding in MODEL_ENCODINGS.items():
        if model.startswith(model_prefix):
            return encoding

    # Default to cl100k_base (most common)
    return "cl100k_base"


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Count tokens in a text string.

    Args:
        text: Text to count tokens for
        model: Model name for appropriate encoding

    Returns:
        Number of tokens
    """
    if not text:
        return 0

    try:
        encoding_name = get_encoding_for_model(model)
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: approximate with word count * 1.3
        return int(len(text.split()) * 1.3)


def count_message_tokens(messages: List[Dict], model: str = "gpt-4o-mini") -> int:
    """
    Count tokens in a messages array (OpenAI format).

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name for appropriate encoding

    Returns:
        Total token count including formatting overhead
    """
    try:
        encoding_name = get_encoding_for_model(model)
        encoding = tiktoken.get_encoding(encoding_name)

        num_tokens = 0

        for message in messages:
            # Tokens for message structure
            num_tokens += 4  # Every message has role/name/content tokens

            role = message.get("role", "")
            content = message.get("content", "")
            name = message.get("name", "")

            num_tokens += len(encoding.encode(role))
            num_tokens += len(encoding.encode(content)) if content else 0
            num_tokens += len(encoding.encode(name)) if name else 0

        # Every reply is primed with assistant role
        num_tokens += 2

        return num_tokens

    except Exception:
        # Fallback: count all text
        total_text = " ".join(
            msg.get("content", "") for msg in messages if msg.get("content")
        )
        return count_tokens(total_text, model)


def estimate_response_tokens(usage: Dict) -> int:
    """
    Extract response token count from OpenAI usage object.

    Args:
        usage: Usage dict from LLM response

    Returns:
        Number of completion tokens
    """
    return usage.get("completion_tokens", 0)


def calculate_memory_tokens(memories: List[Dict], model: str = "gpt-4o-mini") -> int:
    """
    Calculate token count for formatted memory context.

    Args:
        memories: List of memory objects
        model: Model name for appropriate encoding

    Returns:
        Token count for memory context
    """
    if not memories:
        return 0

    # Format memories to count tokens accurately
    memory_texts = []
    for mem in memories:
        content = mem.get("content", "").strip()
        relevance = mem.get("relevance", 0)
        memory_texts.append(f"[{relevance:.2f}] {content}")

    context = "\n".join(memory_texts)
    wrapper = f"<relevant_context>\nThe following information from previous conversations may be relevant:\n\n{context}\n</relevant_context>"

    return count_tokens(wrapper, model)


def get_context_window_size(model: str) -> int:
    """
    Get the context window size for a model.

    Args:
        model: Model name

    Returns:
        Context window size in tokens
    """
    # Common model context windows
    context_windows = {
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4-turbo": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16385,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-haiku": 200000,
        "gemini-pro": 32768,
    }

    # Try exact match
    if model in context_windows:
        return context_windows[model]

    # Try prefix match
    for model_prefix, window_size in context_windows.items():
        if model.startswith(model_prefix):
            return window_size

    # Conservative default
    return 8192


def estimate_tokens_saved(original_tokens: int, enriched_tokens: int, context_modified: bool) -> int:
    """
    Estimate tokens saved by smart memory injection vs sending full history.

    Args:
        original_tokens: Tokens in original messages
        enriched_tokens: Tokens after memory enrichment
        context_modified: Whether memory context was added

    Returns:
        Estimated tokens saved (can be negative if memory added more)
    """
    if not context_modified:
        return 0

    # This is a simplified calculation
    # In practice, we're comparing enriched context vs full conversation history
    # For now, we just track the memory overhead
    memory_overhead = enriched_tokens - original_tokens

    # If we're using memories, we're likely saving tokens by not sending full history
    # Estimate: average conversation history is ~2000 tokens, we add ~500 tokens of memory
    if memory_overhead > 0:
        estimated_history_tokens = 2000
        return estimated_history_tokens - memory_overhead

    return 0
