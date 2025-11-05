"""
Simple usage example of the Memory Router

This demonstrates how to use the router module directly
without running the FastAPI server.
"""
import os
from modules.router import route, memory_route


def main():
    """Simple usage examples"""

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("Run: export OPENAI_API_KEY='sk-...'")
        return

    print("=" * 60)
    print("Memory Router - Simple Usage Example")
    print("=" * 60)

    # ========================================================================
    # Example 1: Simple conversation with memory
    # ========================================================================

    print("\n\n🧠 Example 1: Conversation with Memory")
    print("-" * 60)

    user_id = "demo-user"

    # First message - introduce yourself
    print("\nUser: Hi, my name is John and I'm a software engineer.")

    response1 = route(
        prompt="Hi, my name is John and I'm a software engineer.",
        user_id=user_id,
        api_key=api_key,
        memory_enabled=True
    )

    print(f"Assistant: {response1}")

    # Second message - ask about yourself
    # This should retrieve the memory from the first message
    print("\nUser: What's my name?")

    response2 = route(
        prompt="What's my name?",
        user_id=user_id,
        api_key=api_key,
        memory_enabled=True
    )

    print(f"Assistant: {response2}")

    # ========================================================================
    # Example 2: Using memory_route directly with message history
    # ========================================================================

    print("\n\n💬 Example 2: Multi-turn conversation")
    print("-" * 60)

    messages = [
        {"role": "user", "content": "I'm learning Python and FastAPI"},
        {"role": "assistant", "content": "That's great! FastAPI is excellent for building APIs."},
        {"role": "user", "content": "What was I learning about?"}
    ]

    print("\nConversation:")
    for msg in messages:
        print(f"{msg['role'].title()}: {msg['content']}")

    response = memory_route(
        messages=messages,
        model="gpt-4o-mini",
        user_id=user_id,
        provider_url="https://api.openai.com/v1",
        api_key=api_key,
        memory_enabled=True
    )

    print(f"\nFinal response: {response['choices'][0]['message']['content']}")
    print(f"\nMetadata:")
    print(f"  - Memories retrieved: {response.get('_memory_metadata', {}).get('chunks_retrieved', 0)}")
    print(f"  - Context modified: {response.get('_memory_metadata', {}).get('context_modified', False)}")

    # ========================================================================
    # Example 3: Disable memory
    # ========================================================================

    print("\n\n⚪ Example 3: Without memory (fresh conversation)")
    print("-" * 60)

    response3 = route(
        prompt="What's my name?",
        user_id="different-user",  # Different user, no memory
        api_key=api_key,
        memory_enabled=False  # Explicitly disable memory
    )

    print(f"\nUser: What's my name?")
    print(f"Assistant: {response3}")
    print("(Should not know the name since memory is disabled)")

    print("\n" + "=" * 60)
    print("✅ Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
