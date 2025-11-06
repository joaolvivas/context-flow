# 🧠 Intelligent System Prompt Design

> **Goal**: Make the LLM understand it's operating as a memory-aware orchestrator

---

## Problem Statement

Currently, ContextFlow injects memory context without explaining to the LLM:
- What the context represents
- How the memory system works
- How to use the provided information effectively
- When to acknowledge using memories

**Result**: LLM treats injected context as generic information, not personalized memories.

---

## Proposed Solution: Tiered System Prompt

### Option 1: Minimal (Low Token Cost)

```
You are an AI assistant with access to the user's conversation history and memories.

Context provided above includes:
- Recent conversation turns (Working Memory)
- Extracted facts about the user (Session Memory)
- Long-term knowledge from past interactions (Long-term Memory)

Use this information to provide personalized, contextually-aware responses. Reference specific memories when relevant.
```

**Pros**:
- Low token cost (~60 tokens)
- Clear and concise
- Works with any LLM

**Cons**:
- Doesn't explain the tier system
- Less guidance on how to use memories

---

### Option 2: Detailed (Medium Token Cost) ⭐ **RECOMMENDED**

```
You are an AI assistant with an advanced memory system that helps you provide personalized responses.

## Memory System

You have access to a 3-tier memory architecture:

**Tier 1 - Working Memory** (Recent Context)
- Last 10-20 conversation turns
- Provides immediate context for ongoing discussions
- Always available for continuity

**Tier 2 - Session Memory** (Extracted Facts)
- Key facts extracted from conversations
- Categories: preferences, goals, tools, people, teams, projects, etc.
- Helps you personalize responses without repeating yourself

**Tier 3 - Long-term Memory** (Historical Knowledge)
- Deep memories from past interactions
- Graph-based connections between concepts
- Retrieved only when relevant to current query

## How to Use Memories

1. **Acknowledge context naturally**: Don't say "Based on the memory provided..." - just use the information as if you remember it
2. **Be specific**: Reference actual details from memories when relevant
3. **Update when needed**: If user corrects information, use the new information (it will be stored automatically)
4. **Admit gaps**: If a memory isn't available, honestly say you don't have that information

## Context Provided Above

The context above contains relevant memories for this conversation. Use them to:
- Personalize your responses
- Maintain consistency across conversations
- Avoid asking for information you already know
- Build on previous discussions

Remember: You're having a conversation with someone you know, not a stranger.
```

**Pros**:
- ✅ Explains tier system clearly
- ✅ Provides usage guidelines
- ✅ Encourages natural memory usage
- ✅ Helps LLM understand its role

**Cons**:
- Higher token cost (~250 tokens)
- Might be too detailed for simple queries

**Token Cost**: ~$0.00075 per request (GPT-4o @ $3/1M tokens)

---

### Option 3: Adaptive (Dynamic Based on Query)

Inject different prompts based on query complexity:

**Level 1 queries** (greetings, simple questions):
```
You have access to the user's recent conversation history. Use it for context.
```
(~15 tokens)

**Level 2 queries** (factual recall, preferences):
```
You have access to the user's conversation history and extracted facts. Use this information to provide personalized responses.
```
(~25 tokens)

**Level 3 queries** (complex, deep historical):
```
[Full detailed prompt from Option 2]
```
(~250 tokens)

**Pros**:
- ✅ Cost-efficient (saves tokens on simple queries)
- ✅ Detailed when needed
- ✅ Matches progressive injection philosophy

**Cons**:
- More complex to implement
- Query classification needs to be accurate

---

## Implementation Details

### Where to Inject

**Current location**: `modules/router_v3.py:enrich_messages_with_tiered_context()`

**Current code**:
```python
def enrich_messages_with_tiered_context(
    messages: List[Dict],
    tiered_context: str
) -> List[Dict]:
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
```

**Proposed improvement**:
```python
def enrich_messages_with_tiered_context(
    messages: List[Dict],
    tiered_context: str,
    memory_metadata: Dict = None,
    system_prompt_style: str = "detailed"  # "minimal", "detailed", "adaptive"
) -> List[Dict]:
    if not tiered_context:
        return messages

    enriched = messages.copy()

    # Select system prompt based on style
    system_prompt = get_memory_system_prompt(
        style=system_prompt_style,
        memory_metadata=memory_metadata
    )

    # Combine system prompt + context
    full_system_message = f"{system_prompt}\n\n## Relevant Context\n\n{tiered_context}"

    # Find existing system message
    system_idx = None
    for idx, msg in enumerate(enriched):
        if msg.get("role") == "system":
            system_idx = idx
            break

    if system_idx is not None:
        # Preserve user's system message, append memory system prompt
        enriched[system_idx]["content"] += f"\n\n{full_system_message}"
    else:
        # Insert new system message
        enriched.insert(0, {
            "role": "system",
            "content": full_system_message
        })

    return enriched


def get_memory_system_prompt(style: str, memory_metadata: Dict = None) -> str:
    """Generate appropriate system prompt based on style and metadata"""

    if style == "minimal":
        return """You are an AI assistant with access to the user's conversation history and memories.

Use this information to provide personalized, contextually-aware responses. Reference specific memories when relevant."""

    elif style == "detailed":
        # Customize based on which tiers were actually used
        tiers_used = memory_metadata.get("tiers_used", []) if memory_metadata else []

        prompt = """You are an AI assistant with an advanced memory system that helps you provide personalized responses.

## Memory System

You have access to a 3-tier memory architecture:"""

        if "working_memory" in tiers_used or not tiers_used:
            prompt += """

**Tier 1 - Working Memory** (Recent Context)
- Last 10-20 conversation turns
- Provides immediate context for ongoing discussions"""

        if "session_memory" in tiers_used or not tiers_used:
            prompt += """

**Tier 2 - Session Memory** (Extracted Facts)
- Key facts extracted from conversations
- Categories: preferences, goals, tools, people, teams, projects
- Helps you personalize responses"""

        if "graphiti" in tiers_used or not tiers_used:
            prompt += """

**Tier 3 - Long-term Memory** (Historical Knowledge)
- Deep memories from past interactions
- Graph-based connections between concepts"""

        prompt += """

## How to Use Memories

1. **Acknowledge context naturally**: Don't say "Based on the memory provided..." - just use the information as if you remember it
2. **Be specific**: Reference actual details from memories when relevant
3. **Update when needed**: If user corrects information, use the new information
4. **Admit gaps**: If a memory isn't available, honestly say you don't have that information

Remember: You're having a conversation with someone you know, not a stranger."""

        return prompt

    elif style == "adaptive":
        # Use query level from metadata to decide
        query_level = memory_metadata.get("query_level", 2) if memory_metadata else 2

        if query_level == 1:
            return "You have access to the user's recent conversation history. Use it for context."
        elif query_level == 2:
            return "You have access to the user's conversation history and extracted facts. Use this information to provide personalized responses."
        else:
            return get_memory_system_prompt("detailed", memory_metadata)

    else:
        return get_memory_system_prompt("detailed", memory_metadata)
```

---

## Configuration

Add to `config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Memory system prompt configuration
    memory_system_prompt_style: str = Field(
        default="detailed",
        description="System prompt style: 'minimal', 'detailed', or 'adaptive'"
    )

    memory_system_prompt_custom: Optional[str] = Field(
        default=None,
        description="Custom system prompt (overrides style if provided)"
    )
```

Add to `.env.example`:

```bash
# Memory System Prompt Configuration
MEMORY_SYSTEM_PROMPT_STYLE=detailed  # Options: minimal, detailed, adaptive
# MEMORY_SYSTEM_PROMPT_CUSTOM="Your custom prompt here"
```

---

## Testing & Validation

### A/B Test Metrics

Compare responses **with** vs **without** intelligent system prompt:

**Metrics to track**:
1. **Memory utilization**: Does LLM reference memories more often?
2. **User satisfaction**: Subjective quality of responses
3. **Context awareness**: Does LLM maintain better continuity?
4. **Token efficiency**: Is the extra prompt cost justified?

**Test scenarios**:
- "What's my favorite programming language?" (should use Tier 2 facts)
- "Remember when we discussed X?" (should use Tier 3 long-term memory)
- "Hello" (should not over-rely on memories)

### Success Criteria

✅ LLM references specific memories naturally (no "based on provided context")
✅ Better personalization without token waste
✅ Fewer "I don't know" when memory exists
✅ More consistent across conversations

---

## Cost Analysis

### Option 1 (Minimal): ~60 tokens
- Cost: ~$0.00018 per request (GPT-4o)
- Annual cost at 100K requests: ~$18

### Option 2 (Detailed): ~250 tokens
- Cost: ~$0.00075 per request (GPT-4o)
- Annual cost at 100K requests: ~$75

### Option 3 (Adaptive): ~15-250 tokens (avg ~80)
- Cost: ~$0.00024 per request average (GPT-4o)
- Annual cost at 100K requests: ~$24

**Recommendation**: Start with **Option 2 (Detailed)** for all users. The ~$75/year cost for dramatically better UX is worth it.

---

## Alternatives Considered

### Alternative 1: Post-hoc Explanation
Inject memory context WITHOUT system prompt, then add a user message: "Use the context above to answer my question"

**Pros**: Doesn't consume system message
**Cons**: Awkward UX, user sees the meta-instruction

### Alternative 2: Fine-tuning
Fine-tune the LLM to understand memory context without explicit prompting

**Pros**: Zero ongoing token cost
**Cons**: Requires training data, model-specific, expensive upfront

### Alternative 3: Memory Metadata in Headers
Don't change messages, pass memory metadata in custom headers

**Pros**: No token cost
**Cons**: LLM can't access headers, doesn't help

---

## Rollout Plan

### Phase 1: Prototype (Week 1)
- Implement `get_memory_system_prompt()` function
- Add configuration options
- Test with 10 sample conversations

### Phase 2: Validation (Week 2)
- A/B test: 50% with detailed prompt, 50% without
- Collect feedback from beta users
- Measure memory utilization metrics

### Phase 3: Optimization (Week 3)
- Refine prompt based on feedback
- Implement adaptive style if needed
- Document best practices

### Phase 4: Launch (Week 4)
- Enable for all users
- Set "detailed" as default
- Monitor metrics

---

## Future Enhancements

### 1. User-Customizable Prompts
Allow users to customize the system prompt:
```bash
contextflow config --system-prompt "You are a helpful coding assistant with memory..."
```

### 2. Persona-Based Prompts
Different prompts for different use cases:
- **Code Assistant**: "You're a coding assistant with memory of past projects..."
- **Research Assistant**: "You're a research assistant who remembers sources and findings..."
- **Personal Assistant**: "You're a personal assistant who knows the user's schedule and preferences..."

### 3. Multi-Language Support
Detect user language and inject appropriate system prompt:
- English, Portuguese, Spanish, etc.

### 4. Memory Confidence Indication
Include confidence scores in system prompt:
```
**Tier 2 - Session Memory** (confidence: 85%)
- User prefers Python (mentioned 3 times)
- Works at Acme Corp (mentioned 1 time, not recently confirmed)
```

---

## Related Improvements

This system prompt enhancement pairs well with:
1. **Memory Analytics** (show users what's being injected)
2. **Feedback Loop** (did the LLM use memories correctly?)
3. **Memory Pruning** (remove outdated/incorrect memories)
4. **Context Compression** (summarize long memories before injection)

---

## Open Questions

1. Should the prompt vary by model? (GPT-4 vs Claude vs Gemini)
2. Should we mention the token savings to the LLM?
3. How do we handle conflicts between user's system message and ours?
4. Should we add examples of good memory usage to the prompt?

---

## References

- Progressive Injection design: `PROGRESSIVE_INJECTION.md`
- Current implementation: `modules/router_v3.py:enrich_messages_with_tiered_context()`
- Memory system: `modules/memory/intelligent_router.py`

---

**Status**: 🎯 Ready for implementation
**Priority**: 🔥 High (significantly improves UX)
**Effort**: 📅 1-2 days
**Impact**: 🚀 High (better memory utilization, more personalized responses)
