#!/bin/bash
# Test Progressive Context Injection
# Tests all 3 tier levels to verify token optimization

BASE_URL="http://localhost:8000"
API_KEY="${OPENAI_API_KEY}"

echo "=========================================="
echo "Progressive Context Injection Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Tier 1 Only (90% of queries - simple continuation)
echo -e "${YELLOW}Test 1: Tier 1 Only Query${NC}"
echo "Query: 'Hello, how are you?'"
echo "Expected: working_memory only (~100-200 tokens)"
echo ""

curl -s -X POST "$BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }' | jq '._memory_metadata // "No metadata"'

echo ""
echo "---"
echo ""

# Test 2: Tier 1 + 2 (8% of queries - factual query)
echo -e "${YELLOW}Test 2: Tier 1 + 2 Query${NC}"
echo "Query: 'What is my favorite color?'"
echo "Expected: working_memory + session_facts (~300-400 tokens)"
echo ""

curl -s -X POST "$BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "My favorite color is blue"},
      {"role": "assistant", "content": "Got it! Your favorite color is blue."},
      {"role": "user", "content": "What is my favorite color?"}
    ]
  }' | jq '._memory_metadata // "No metadata"'

echo ""
echo "---"
echo ""

# Test 3: All Tiers (2% of queries - deep/historical)
echo -e "${YELLOW}Test 3: All Tiers Query${NC}"
echo "Query: 'Remember when we talked about my preferences?'"
echo "Expected: working_memory + session_facts + graphiti (~800-1500 tokens)"
echo ""

curl -s -X POST "$BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Remember when we talked about my preferences before?"}
    ]
  }' | jq '._memory_metadata // "No metadata"'

echo ""
echo "---"
echo ""

# Test 4: Very short query (should use Tier 1 + 2)
echo -e "${YELLOW}Test 4: Very Short Query${NC}"
echo "Query: 'My name is João'"
echo "Expected: Tier 1 + 2 (short queries are often factual)"
echo ""

curl -s -X POST "$BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "My name is João"}
    ]
  }' | jq '._memory_metadata // "No metadata"'

echo ""
echo "=========================================="
echo "Checking Logs for Tier Usage"
echo "=========================================="
echo ""

# Show recent tier usage from logs
echo -e "${GREEN}Last 10 tier usage patterns:${NC}"
grep -E "(Memory tiers used|tier_level)" /tmp/proxy_v3.log | tail -10

echo ""
echo "=========================================="
echo "Checking Redis Storage"
echo "=========================================="
echo ""

# Check Tier 1 storage
echo -e "${GREEN}Tier 1 (Working Memory):${NC}"
redis-cli -n 0 KEYS "conversation:*" | head -5

echo ""
# Check Tier 2 storage
echo -e "${GREEN}Tier 2 (Session Facts):${NC}"
redis-cli -n 1 KEYS "session:*" | head -5

echo ""
echo "=========================================="
echo "Token Cost Comparison"
echo "=========================================="
echo ""

echo "Expected token savings with progressive injection:"
echo ""
echo "Before (all tiers always):"
echo "  Average: ~700 tokens per query"
echo ""
echo "After (progressive):"
echo "  90% queries (Tier 1): ~200 tokens"
echo "  8% queries (Tier 1+2): ~400 tokens"
echo "  2% queries (All): ~1000 tokens"
echo "  Weighted average: (0.9*200) + (0.08*400) + (0.02*1000) = 232 tokens"
echo ""
echo -e "${GREEN}Expected savings: ~67% reduction in token costs!${NC}"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="
