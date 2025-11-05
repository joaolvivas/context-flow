#!/bin/bash
# Fast startup using uv (much faster than pip)

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Proxy Orchestrator (Fast Mode with uv)${NC}\n"

# Check config
if [ ! -f "python-proxy/.env" ]; then
    echo -e "${YELLOW}⚠️  Creating .env from template...${NC}"
    cp python-proxy/.env.example python-proxy/.env
fi

# Kill existing processes
lsof -ti:5001 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

echo -e "${BLUE}Starting HTTP Bridge (Port 5001)...${NC}"
cd "$(dirname "$0")"

# Use uv for bridge (reuse Graphiti deps)
MCP_PORT=5001 uv run --directory /Users/joaolucas/graphiti/mcp_server \
  python "$(pwd)/graphiti_http_bridge.py" > bridge.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > bridge.pid
echo -e "${GREEN}✓ HTTP Bridge started (PID: $BRIDGE_PID)${NC}"

sleep 3

echo -e "${BLUE}Starting Memory Proxy (Port 8000)...${NC}"
cd python-proxy

# Use uv for proxy too
uv run --with fastapi --with uvicorn --with pydantic-settings \
  --with httpx --with requests --with tiktoken --with neo4j \
  --with slowapi --with structlog \
  python main.py > proxy.log 2>&1 &
PROXY_PID=$!
echo $PROXY_PID > proxy.pid
echo -e "${GREEN}✓ Memory Proxy started (PID: $PROXY_PID)${NC}"

sleep 2

# Test endpoints
echo -e "\n${BLUE}Testing endpoints...${NC}"
if curl -s http://localhost:5001/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ HTTP Bridge: http://localhost:5001${NC}"
else
    echo -e "${YELLOW}⚠ HTTP Bridge may still be starting...${NC}"
fi

if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✓ Memory Proxy: http://localhost:8000${NC}"
else
    echo -e "${YELLOW}⚠ Memory Proxy may still be starting...${NC}"
fi

echo -e "\n${GREEN}✅ System ready!${NC}"
echo -e "\n📖 Usage:"
echo "  Msty: Set base URL to http://localhost:8000/v1"
echo "  Test: curl http://localhost:8000/health"
echo "  Logs: tail -f python-proxy/proxy.log"
echo "  Stop: ./stop.sh"
echo ""
