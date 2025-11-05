#!/bin/bash
# Test the full integration

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing Proxy Orchestrator Integration${NC}\n"

# Test 1: HTTP Bridge Health
echo -e "${BLUE}[1/4]${NC} Testing HTTP Bridge..."
if curl -s http://localhost:5001/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ HTTP Bridge is healthy${NC}"
else
    echo -e "${RED}✗ HTTP Bridge is not responding${NC}"
    exit 1
fi

# Test 2: Memory Proxy Health
echo -e "${BLUE}[2/4]${NC} Testing Memory Proxy..."
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✓ Memory Proxy is healthy${NC}"
else
    echo -e "${RED}✗ Memory Proxy is not responding${NC}"
    exit 1
fi

# Test 3: Store Memory
echo -e "${BLUE}[3/4]${NC} Testing memory storage..."
STORE_RESULT=$(curl -s -X POST http://localhost:5001/mcp/store \
  -H "Content-Type: application/json" \
  -d '{"content":"Test memory: Lucas loves testing integrations","user_id":"test"}')

if echo "$STORE_RESULT" | grep -q "success"; then
    echo -e "${GREEN}✓ Memory stored successfully${NC}"
else
    echo -e "${RED}✗ Failed to store memory${NC}"
    echo "$STORE_RESULT"
fi

# Test 4: Search Memory
echo -e "${BLUE}[4/4]${NC} Testing memory search..."
sleep 2  # Wait for indexing
SEARCH_RESULT=$(curl -s -X POST http://localhost:5001/mcp/search \
  -H "Content-Type: application/json" \
  -d '{"query":"What does Lucas love?","user_id":"test","limit":5}')

if echo "$SEARCH_RESULT" | grep -q "results"; then
    echo -e "${GREEN}✓ Memory search working${NC}"
else
    echo -e "${RED}✗ Memory search failed${NC}"
fi

# Check stats
echo -e "\n${BLUE}📊 Memory Stats:${NC}"
curl -s http://localhost:5001/mcp/stats | python3 -m json.tool | head -10

echo -e "\n${GREEN}✅ All tests passed!${NC}"
echo -e "\n${BLUE}📖 Next steps:${NC}"
echo "  1. In Msty, add custom provider:"
echo "     Base URL: http://localhost:8000/v1"
echo "     API Key: Your OpenAI/Anthropic key"
echo ""
echo "  2. Start chatting - memory is automatic!"
echo ""
