#!/usr/bin/env python3
"""
Test script for Tier 2 fact extraction

Usage:
    python test_session_memory.py <your-openai-api-key>
"""
import sys
import os
from modules.memory.session_memory import SessionMemory

def test_fact_extraction(api_key):
    """Test fact extraction with provided API key"""
    print("Testing Tier 2 fact extraction...")
    print("=" * 60)

    # Initialize session memory
    session_mem = SessionMemory(
        redis_host="localhost",
        redis_port=6379,
        redis_db=1,
        openai_api_key=api_key,
        model="gpt-4o-mini"
    )

    # Test data
    user_msg = "My favorite color is blue and my dog's name is Max"
    assistant_msg = "That's lovely! Blue is a great color, and Max sounds like a wonderful dog!"

    print(f"\nTest conversation:")
    print(f"  User: {user_msg}")
    print(f"  Assistant: {assistant_msg}")
    print()

    # Extract facts
    print("Extracting facts...")
    facts = session_mem.extract_facts(user_msg, assistant_msg)

    print(f"\nExtracted {len(facts)} facts:")
    for i, fact in enumerate(facts, 1):
        print(f"  {i}. [{fact.get('category', 'N/A')}] {fact.get('fact', 'N/A')}")

    if len(facts) > 0:
        print("\n✅ SUCCESS: Fact extraction is working!")

        # Test storage
        print("\nTesting Redis storage...")
        stored = session_mem.store_facts("test_user", "test_conv", facts)
        print(f"Stored {stored} facts")

        # Test retrieval
        print("\nTesting retrieval...")
        retrieved = session_mem.get_facts("test_user", "test_conv")
        print(f"Retrieved {len(retrieved)} facts")

        # Cleanup
        print("\nCleaning up test data...")
        session_mem.redis_client.delete("session_facts:test_user:test_conv")
        print("Done!")

        return True
    else:
        print("\n❌ FAILED: No facts extracted")
        print("\nPossible issues:")
        print("  1. Invalid API key")
        print("  2. OpenAI API error")
        print("  3. Network connectivity issue")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_session_memory.py <your-openai-api-key>")
        print("\nOr set OPENAI_API_KEY environment variable:")
        print("  export OPENAI_API_KEY=sk-...")
        print("  python test_session_memory.py")
        sys.exit(1)

    api_key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("OPENAI_API_KEY")

    if not api_key or api_key.startswith("<"):
        print("❌ Error: Please provide a valid OpenAI API key")
        sys.exit(1)

    success = test_fact_extraction(api_key)
    sys.exit(0 if success else 1)
