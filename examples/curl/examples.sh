#!/bin/bash
# MemoryStack - cURL Examples
# Test MemoryStack without any SDK - just HTTP requests

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_KEY="sk-your-openai-api-key"
BASE_URL="http://localhost:8000"
USER_ID="charlie"

echo -e "${BLUE}=== MemoryStack cURL Examples ===${NC}\n"

# Example 1: Health Check
echo -e "${BLUE}1. Health Check${NC}"
curl -s http://localhost:8000/health | jq .
echo -e "\n"

# Example 2: Simple Chat (Store Information)
echo -e "${BLUE}2. Store Information${NC}"
curl -s -X POST "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-User-Id: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "My name is Charlie and I work as a software engineer at TechCorp"}
    ]
  }' | jq -r '.choices[0].message.content'
echo -e "\n"

# Example 3: Retrieve Information (Test Memory)
echo -e "${BLUE}3. Test Memory Retrieval${NC}"
curl -s -X POST "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-User-Id: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "What is my name and where do I work?"}
    ]
  }' | jq -r '.choices[0].message.content'
echo -e "\n"

# Example 4: Get Diagnostic Headers
echo -e "${BLUE}4. Memory Diagnostics${NC}"
curl -s -i -X POST "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-User-Id: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Quick test"}
    ]
  }' | grep -i "X-Memory-" | head -10
echo -e "\n"

# Example 5: Disable Memory for Specific Request
echo -e "${BLUE}5. Disable Memory (Private Message)${NC}"
curl -s -X POST "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-User-Id: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "This is a secret message, do not store it"}
    ],
    "memory_enabled": false
  }' | jq -r '.choices[0].message.content'
echo -e "\n"

# Example 6: Custom Conversation ID
echo -e "${BLUE}6. Custom Conversation ID${NC}"
curl -s -X POST "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-User-Id: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "I am having a conversation in Project Alpha"}
    ],
    "conversation_id": "project-alpha-chat"
  }' | jq -r '.choices[0].message.content'
echo -e "\n"

# Example 7: Test Progressive Injection (Different Query Types)
echo -e "${BLUE}7. Progressive Injection Test${NC}"

echo -e "${GREEN}Level 1 Query (Simple):${NC}"
curl -s -X POST "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-User-Id: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  }' | jq -r '.choices[0].message.content'

echo -e "\n${GREEN}Level 2 Query (Factual):${NC}"
curl -s -X POST "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-User-Id: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "What is my job?"}]
  }' | jq -r '.choices[0].message.content'

echo -e "\n${GREEN}Level 3 Query (Deep):${NC}"
curl -s -X POST "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-User-Id: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Tell me everything you remember about me"}]
  }' | jq -r '.choices[0].message.content'

echo -e "\n${GREEN}✅ All examples completed!${NC}"
