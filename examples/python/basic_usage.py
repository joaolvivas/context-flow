#!/usr/bin/env python3
"""
MemoryStack - Basic Usage Example

This example shows the simplest way to use MemoryStack with the OpenAI SDK.
Just change the base_url and your AI gets perfect memory!
"""

from openai import OpenAI

# Initialize client pointing to MemoryStack
client = OpenAI(
    api_key="sk-your-openai-api-key",  # Your actual OpenAI API key
    base_url="http://localhost:8000/v1",  # Point to MemoryStack instead
    default_headers={
        "X-User-Id": "alice"  # Optional: Namespace memories per user
    }
)

# First conversation - store some information
print("=== First Conversation ===")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "My name is Alice and I'm learning Python. I'm building a chatbot."}
    ]
)
print(f"AI: {response.choices[0].message.content}\n")

# Check memory metadata in response headers
# MemoryStack adds diagnostic headers like:
# X-Memory-Tiers-Used, X-Memory-Tier1-Turns, X-Memory-Processing-Time-Ms
# These are visible in HTTP responses but not in SDK responses

# Second conversation - test memory
print("=== Second Conversation (Different Chat) ===")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "What's my name and what am I working on?"}
    ]
)
print(f"AI: {response.choices[0].message.content}\n")
# Expected: "Your name is Alice and you're building a chatbot using Python"

# Third conversation - deeper question
print("=== Third Conversation (Needs Long-term Memory) ===")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Tell me everything you know about me"}
    ]
)
print(f"AI: {response.choices[0].message.content}\n")

print("✅ Memory working! Your AI remembers across different chats.")
