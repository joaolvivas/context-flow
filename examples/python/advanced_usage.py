#!/usr/bin/env python3
"""
MemoryStack - Advanced Usage Example

Shows streaming, custom configuration, and memory control.
"""

from openai import OpenAI
import httpx

# Initialize with custom configuration
client = OpenAI(
    api_key="sk-your-openai-api-key",
    base_url="http://localhost:8000/v1",
    default_headers={
        "X-User-Id": "bob",  # Different user = different memory namespace
    }
)

# Example 1: Streaming responses with memory
print("=== Streaming Example ===")
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "I love hiking in the mountains."}
    ],
    stream=True
)

print("AI: ", end="")
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print("\n")

# Example 2: Using different models with same memory
print("\n=== Multi-Model Example ===")

# Chat with GPT-4o-mini
response1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What do I love to do?"}]
)
print(f"GPT-4o-mini: {response1.choices[0].message.content}")

# Chat with GPT-4 (memory persists!)
response2 = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What do I love to do?"}]
)
print(f"GPT-4: {response2.choices[0].message.content}")

# Example 3: Disable memory for specific requests
print("\n=== Memory Control Example ===")

# Make a direct HTTP request to control memory
response = httpx.post(
    "http://localhost:8000/chat/completions",
    headers={
        "Authorization": "Bearer sk-your-openai-api-key",
        "X-User-Id": "bob",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "This is private, don't remember it"}
        ],
        "memory_enabled": False  # Disable memory for this request
    }
)

result = response.json()
print(f"AI (no memory): {result['choices'][0]['message']['content']}")

# Check diagnostic headers
print("\n=== Memory Diagnostics ===")
for header, value in response.headers.items():
    if header.startswith("X-Memory-"):
        print(f"{header}: {value}")

print("\n✅ Advanced features working!")
