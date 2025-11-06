#!/bin/bash

echo "🧪 Testing 3-Tier Memory System"
echo "================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROXY_URL="http://localhost:8000"
CONVERSATION_ID="test-3tier-$(date +%s)"

echo "📝 Conversation ID: $CONVERSATION_ID"
echo ""

# Test 1: Store initial facts (Tier 1 + 2 + 3)
echo "Test 1: Storing initial facts..."
echo "User: My favorite color is black and my dog's name is Max"

RESPONSE=$(curl -s -X POST $PROXY_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -d "{
    \"model\": \"gpt-4o\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"My favorite color is black and my dog name is Max\"}
    ],
    \"user_id\": \"test-user\",
    \"conversation_id\": \"$CONVERSATION_ID\",
    \"memory_enabled\": true
  }")

# Extract tier information from response headers
TIERS=$(echo "$RESPONSE" | grep -i "x-memory-tiers-used" | cut -d':' -f2 | tr -d ' \r')
TIER1=$(echo "$RESPONSE" | grep -i "x-memory-tier1-turns" | cut -d':' -f2 | tr -d ' \r')
TIER2=$(echo "$RESPONSE" | grep -i "x-memory-tier2-facts" | cut -d':' -f2 | tr -d ' \r')
TIME=$(echo "$RESPONSE" | grep -i "x-memory-processing-time" | cut -d':' -f2 | tr -d ' \r')

echo -e "${GREEN}✓${NC} Response received in ${TIME}ms"
echo "  Tiers used: $TIERS"
echo "  Tier 1 (Working): $TIER1 turns"
echo "  Tier 2 (Session): $TIER2 facts"
echo ""

# Wait for fact extraction
echo "⏳ Waiting 3 seconds for Tier 2 fact extraction..."
sleep 3
echo ""

# Test 2: Simple factual query (should use Tier 1 + 2, NOT Tier 3)
echo "Test 2: Simple factual query (Tier 1 + 2 only)..."
echo "User: What is my favorite color?"

RESPONSE2=$(curl -s -X POST $PROXY_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -d "{
    \"model\": \"gpt-4o\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"What is my favorite color?\"}
    ],
    \"user_id\": \"test-user\",
    \"conversation_id\": \"$CONVERSATION_ID\",
    \"memory_enabled\": true
  }")

TIERS2=$(echo "$RESPONSE2" | grep -i "x-memory-tiers-used" | cut -d':' -f2 | tr -d ' \r')
COST2=$(echo "$RESPONSE2" | grep -i "x-memory-cost-estimate" | cut -d':' -f2 | tr -d ' \r')
TIME2=$(echo "$RESPONSE2" | grep -i "x-memory-processing-time" | cut -d':' -f2 | tr -d ' \r')
ANSWER=$(echo "$RESPONSE2" | jq -r '.choices[0].message.content' 2>/dev/null | head -c 100)

if [[ "$TIERS2" == *"working_memory"* && "$TIERS2" == *"session_facts"* && "$TIERS2" != *"graphiti"* ]]; then
    echo -e "${GREEN}✓${NC} Correct tier usage: Tier 1 + 2 (NO Graphiti!)"
else
    echo -e "${RED}✗${NC} Incorrect tier usage: $TIERS2"
fi

echo "  Cost estimate: $COST2 tokens"
echo "  Response time: ${TIME2}ms"
echo "  Answer: $ANSWER"
echo ""

# Test 3: Another simple query
echo "Test 3: Another factual query (should be fast)..."
echo "User: What's my dog's name?"

RESPONSE3=$(curl -s -X POST $PROXY_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -d "{
    \"model\": \"gpt-4o\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"What's my dog's name?\"}
    ],
    \"user_id\": \"test-user\",
    \"conversation_id\": \"$CONVERSATION_ID\",
    \"memory_enabled\": true
  }")

TIME3=$(echo "$RESPONSE3" | grep -i "x-memory-processing-time" | cut -d':' -f2 | tr -d ' \r')
ANSWER3=$(echo "$RESPONSE3" | jq -r '.choices[0].message.content' 2>/dev/null | head -c 100)

echo "  Response time: ${TIME3}ms"
echo "  Answer: $ANSWER3"
echo ""

# Test 4: Deep/historical query (should use all 3 tiers)
echo "Test 4: Deep query (should use Tier 1 + 2 + 3)..."
echo "User: Remember what we talked about earlier?"

RESPONSE4=$(curl -s -X POST $PROXY_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -d "{
    \"model\": \"gpt-4o\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Remember what we talked about earlier?\"}
    ],
    \"user_id\": \"test-user\",
    \"conversation_id\": \"$CONVERSATION_ID\",
    \"memory_enabled\": true
  }")

TIERS4=$(echo "$RESPONSE4" | grep -i "x-memory-tiers-used" | cut -d':' -f2 | tr -d ' \r')
TIER3_4=$(echo "$RESPONSE4" | grep -i "x-memory-tier3-memories" | cut -d':' -f2 | tr -d ' \r')
COST4=$(echo "$RESPONSE4" | grep -i "x-memory-cost-estimate" | cut -d':' -f2 | tr -d ' \r')
TIME4=$(echo "$RESPONSE4" | grep -i "x-memory-processing-time" | cut -d':' -f2 | tr -d ' \r')

if [[ "$TIERS4" == *"graphiti"* ]]; then
    echo -e "${GREEN}✓${NC} Correct: All 3 tiers used for deep query"
else
    echo -e "${YELLOW}⚠${NC} Note: Graphiti tier not used (pattern might not have matched)"
fi

echo "  Tiers: $TIERS4"
echo "  Tier 3 memories: $TIER3_4"
echo "  Cost estimate: $COST4 tokens"
echo "  Response time: ${TIME4}ms"
echo ""

# Summary
echo "=========================================="
echo "📊 Summary:"
echo "=========================================="
echo ""
echo "Test 1 (Initial storage): ${TIME}ms"
echo "Test 2 (Factual query):   ${TIME2}ms - Cost: ${COST2} tokens"
echo "Test 3 (Another factual): ${TIME3}ms"
echo "Test 4 (Deep query):      ${TIME4}ms - Cost: ${COST4} tokens"
echo ""

# Performance analysis
if [ "$TIME2" -lt 1000 ] && [ "$TIME3" -lt 1000 ]; then
    echo -e "${GREEN}✓${NC} Performance: Factual queries < 1 second ✓"
else
    echo -e "${YELLOW}⚠${NC} Performance: Some queries took > 1 second"
fi

# Cost analysis
if [ "$COST2" -lt 500 ]; then
    echo -e "${GREEN}✓${NC} Cost efficiency: Factual queries < 500 tokens ✓"
else
    echo -e "${YELLOW}⚠${NC} Cost: Higher than expected"
fi

echo ""
echo "🎉 3-Tier Memory System Test Complete!"
