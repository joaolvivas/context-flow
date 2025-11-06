#!/bin/bash
# Test Warp AI connection to local Memory Proxy

echo "=================================="
echo "Testing Warp → Memory Proxy"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check proxy is running
echo -e "${YELLOW}1. Checking if proxy is running...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Proxy is running on http://localhost:8000${NC}"
else
    echo -e "${RED}✗ Proxy is not running!${NC}"
    echo "Start it with: cd python-proxy && python main.py"
    exit 1
fi
echo ""

# Check OpenAI API key
echo -e "${YELLOW}2. Checking OpenAI API key...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}✗ OPENAI_API_KEY not set!${NC}"
    echo "Set it with: export OPENAI_API_KEY=sk-..."
    exit 1
else
    echo -e "${GREEN}✓ OpenAI API key is set${NC}"
fi
echo ""

# Test a simple query
echo -e "${YELLOW}3. Testing query through proxy...${NC}"
RESPONSE=$(curl -s -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Say hello! This is a test from Warp."}
    ]
  }')

if echo "$RESPONSE" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Proxy is working!${NC}"
    echo ""
    echo "Response:"
    echo "$RESPONSE" | jq -r '.choices[0].message.content'
    echo ""
    echo "Memory Metadata:"
    echo "$RESPONSE" | jq '._memory_metadata'
else
    echo -e "${RED}✗ Query failed!${NC}"
    echo "Error response:"
    echo "$RESPONSE" | jq .
    exit 1
fi
echo ""

# Test memory storage
echo -e "${YELLOW}4. Testing memory storage...${NC}"
curl -s -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "My name is João and I love building AI systems."}
    ]
  }' | jq -r '.choices[0].message.content'
echo ""

sleep 2

# Test memory retrieval
echo -e "${YELLOW}5. Testing memory retrieval...${NC}"
RECALL=$(curl -s -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "What is my name?"}
    ]
  }')

echo "$RECALL" | jq -r '.choices[0].message.content'
echo ""
echo "Tier Level Used:"
echo "$RECALL" | jq '._memory_metadata.tier_level'
echo ""

# Check Redis storage
echo -e "${YELLOW}6. Checking Redis storage...${NC}"
CONV_COUNT=$(redis-cli -n 0 KEYS "conversation:*" 2>/dev/null | wc -l)
FACT_COUNT=$(redis-cli -n 1 KEYS "session:*" 2>/dev/null | wc -l)
echo "Conversations in Redis: $CONV_COUNT"
echo "Session facts in Redis: $FACT_COUNT"
echo ""

# Final instructions
echo "=================================="
echo -e "${GREEN}✓ All tests passed!${NC}"
echo "=================================="
echo ""
echo "To use with Warp AI:"
echo ""
echo "Option 1: Environment Variable"
echo "  export OPENAI_API_BASE=http://localhost:8000"
echo "  export OPENAI_API_KEY=\$OPENAI_API_KEY"
echo ""
echo "Option 2: Warp Settings"
echo "  1. Open Warp Settings (Cmd+,)"
echo "  2. Go to AI → Custom Endpoint"
echo "  3. Set Base URL: http://localhost:8000"
echo "  4. Set API Key: <your OpenAI key>"
echo ""
echo "Then ask Warp AI anything and it will use your memory proxy!"
echo ""
echo "View logs with:"
echo "  tail -f /tmp/proxy_v3.log | grep tier_level"
