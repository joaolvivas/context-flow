"""
Intelligent chunking for long messages

Splits long messages into semantic chunks for better memory storage and retrieval.
Similar to Supermemory's chunking strategy.
"""
import re
from typing import List, Dict
from contextflow.modules.token_counter import count_tokens


# Chunk size limits (in tokens)
DEFAULT_CHUNK_SIZE = 500
MAX_CHUNK_SIZE = 1000
MIN_CHUNK_SIZE = 100


def split_by_sentences(text: str) -> List[str]:
    """
    Split text into sentences using regex.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def split_by_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs.

    Args:
        text: Input text

    Returns:
        List of paragraphs
    """
    paragraphs = text.split('\n\n')
    return [p.strip() for p in paragraphs if p.strip()]


def split_by_code_blocks(text: str) -> List[str]:
    """
    Split text preserving code blocks.

    Args:
        text: Input text

    Returns:
        List of text chunks (with code blocks preserved)
    """
    # Pattern to match code blocks (```...```)
    code_block_pattern = r'```[\s\S]*?```'

    chunks = []
    last_end = 0

    # Find all code blocks
    for match in re.finditer(code_block_pattern, text):
        # Add text before code block
        before_text = text[last_end:match.start()].strip()
        if before_text:
            chunks.append(before_text)

        # Add code block
        chunks.append(match.group())
        last_end = match.end()

    # Add remaining text
    remaining = text[last_end:].strip()
    if remaining:
        chunks.append(remaining)

    return chunks


def chunk_text(
    text: str,
    model: str = "gpt-4o-mini",
    max_chunk_tokens: int = DEFAULT_CHUNK_SIZE
) -> List[Dict]:
    """
    Split text into semantic chunks with metadata.

    Strategy:
    1. Try to split by paragraphs first
    2. If paragraphs are too large, split by sentences
    3. Preserve code blocks as single chunks
    4. Keep chunk sizes within token limits

    Args:
        text: Input text to chunk
        model: Model name for token counting
        max_chunk_tokens: Maximum tokens per chunk

    Returns:
        List of chunk dicts with 'content', 'tokens', 'index'
    """
    if not text or not text.strip():
        return []

    # Check if text is short enough
    total_tokens = count_tokens(text, model)
    if total_tokens <= max_chunk_tokens:
        return [{
            "content": text,
            "tokens": total_tokens,
            "index": 0
        }]

    chunks = []

    # Step 1: Split by code blocks (preserve them)
    code_aware_chunks = split_by_code_blocks(text)

    for section in code_aware_chunks:
        # Check if this is a code block
        if section.startswith('```'):
            # Keep code block as single chunk (even if large)
            chunks.append(section)
            continue

        # Step 2: Try splitting by paragraphs
        paragraphs = split_by_paragraphs(section)

        for para in paragraphs:
            para_tokens = count_tokens(para, model)

            if para_tokens <= max_chunk_tokens:
                # Paragraph fits in one chunk
                chunks.append(para)
            else:
                # Step 3: Split by sentences
                sentences = split_by_sentences(para)

                current_chunk = []
                current_tokens = 0

                for sentence in sentences:
                    sentence_tokens = count_tokens(sentence, model)

                    # If single sentence is too large, just add it as is
                    if sentence_tokens > MAX_CHUNK_SIZE:
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))
                            current_chunk = []
                            current_tokens = 0

                        chunks.append(sentence)
                        continue

                    # Check if adding sentence exceeds limit
                    if current_tokens + sentence_tokens > max_chunk_tokens:
                        # Save current chunk
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))

                        # Start new chunk
                        current_chunk = [sentence]
                        current_tokens = sentence_tokens
                    else:
                        current_chunk.append(sentence)
                        current_tokens += sentence_tokens

                # Add remaining sentences
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

    # Convert to dict format with metadata
    result = []
    for idx, chunk_text in enumerate(chunks):
        if chunk_text.strip():
            result.append({
                "content": chunk_text.strip(),
                "tokens": count_tokens(chunk_text, model),
                "index": idx
            })

    return result


def chunk_conversation(
    messages: List[Dict],
    model: str = "gpt-4o-mini",
    max_chunk_tokens: int = DEFAULT_CHUNK_SIZE
) -> List[Dict]:
    """
    Chunk an entire conversation for memory storage.

    Strategy:
    - Group messages by role (keep user-assistant pairs together)
    - Chunk long individual messages
    - Preserve conversation flow

    Args:
        messages: List of message dicts
        model: Model name for token counting
        max_chunk_tokens: Max tokens per chunk

    Returns:
        List of chunk dicts with 'content', 'tokens', 'messages', 'index'
    """
    chunks = []
    chunk_index = 0

    # Process messages in pairs when possible
    i = 0
    while i < len(messages):
        msg = messages[i]
        role = msg.get("role", "")
        content = msg.get("content", "")

        # Check if we can pair with next message
        if i + 1 < len(messages):
            next_msg = messages[i + 1]
            next_role = next_msg.get("role", "")
            next_content = next_msg.get("content", "")

            # Try to keep user-assistant pairs together
            if (role == "user" and next_role == "assistant") or \
               (role == "assistant" and next_role == "user"):

                pair_content = f"{role.title()}: {content}\n{next_role.title()}: {next_content}"
                pair_tokens = count_tokens(pair_content, model)

                if pair_tokens <= max_chunk_tokens:
                    # Keep pair together
                    chunks.append({
                        "content": pair_content,
                        "tokens": pair_tokens,
                        "messages": [msg, next_msg],
                        "index": chunk_index
                    })
                    chunk_index += 1
                    i += 2
                    continue

        # Single message - chunk if needed
        message_text = f"{role.title()}: {content}"
        message_chunks = chunk_text(message_text, model, max_chunk_tokens)

        for chunk in message_chunks:
            chunks.append({
                "content": chunk["content"],
                "tokens": chunk["tokens"],
                "messages": [msg],
                "index": chunk_index
            })
            chunk_index += 1

        i += 1

    return chunks


def should_chunk(text: str, model: str = "gpt-4o-mini", threshold: int = DEFAULT_CHUNK_SIZE) -> bool:
    """
    Determine if text should be chunked.

    Args:
        text: Input text
        model: Model name for token counting
        threshold: Token threshold for chunking

    Returns:
        True if text should be chunked
    """
    return count_tokens(text, model) > threshold
