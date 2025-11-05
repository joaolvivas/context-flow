#!/bin/bash
# Memory System Startup Script
# Use this to start all services after Mac reboot

set -e

echo "🚀 Starting Memory System (3-Tier Architecture)"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo -e "${RED}❌ Redis not installed. Install with: brew install redis${NC}"
    exit 1
fi

# Check if Python venv exists
if [ ! -d "python-proxy/venv" ]; then
    echo -e "${YELLOW}⚠️  Python venv not found. Creating...${NC}"
    cd python-proxy
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# 1. Start Redis
echo -e "${YELLOW}[1/3] Starting Redis...${NC}"
if brew services list | grep -q "redis.*started"; then
    echo -e "${GREEN}✅ Redis already running${NC}"
else
    brew services start redis
    sleep 2
    echo -e "${GREEN}✅ Redis started${NC}"
fi

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis responding to ping${NC}"
else
    echo -e "${RED}❌ Redis not responding${NC}"
    exit 1
fi

echo ""

# 2. Start Graphiti HTTP Wrapper
echo -e "${YELLOW}[2/3] Starting Graphiti HTTP Wrapper...${NC}"

# Check if already running
if lsof -ti:5001 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Graphiti HTTP Wrapper already running on port 5001${NC}"
else
    # Navigate to graphiti directory
    if [ -d "/Users/joaolucas/graphiti/mcp_server" ]; then
        cd /Users/joaolucas/graphiti/mcp_server
        HTTP_PORT=5001 uv run python http_wrapper.py > /tmp/http_wrapper.log 2>&1 &
        sleep 3

        if lsof -ti:5001 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Graphiti HTTP Wrapper started on port 5001${NC}"
        else
            echo -e "${RED}❌ Failed to start Graphiti HTTP Wrapper${NC}"
            echo "Check logs: tail -f /tmp/http_wrapper.log"
            exit 1
        fi
        cd - > /dev/null
    else
        echo -e "${RED}❌ Graphiti directory not found at /Users/joaolucas/graphiti/mcp_server${NC}"
        exit 1
    fi
fi

echo ""

# 3. Start Memory Proxy
echo -e "${YELLOW}[3/3] Starting Memory Proxy...${NC}"

# Check if already running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8000 already in use. Stopping...${NC}"
    lsof -ti:8000 | xargs kill -9
    sleep 2
fi

# Start the proxy
cd "/Users/joaolucas/Desktop/Proxy Orchestrator/proxy-orchestrator/python-proxy"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found in python-proxy/${NC}"
    echo "Please create .env with:"
    echo "  OPENAI_API_KEY=your-key"
    echo "  DEFAULT_USER_ID=lucas-ai"
    exit 1
fi

./venv/bin/python main.py > /tmp/proxy_v3.log 2>&1 &
PROXY_PID=$!
sleep 3

if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Memory Proxy started on port 8000 (PID: $PROXY_PID)${NC}"
else
    echo -e "${RED}❌ Failed to start Memory Proxy${NC}"
    echo "Check logs: tail -f /tmp/proxy_v3.log"
    exit 1
fi

cd - > /dev/null

echo ""
echo "================================================"
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo ""
echo "Services:"
echo "  ✅ Redis:              localhost:6379"
echo "  ✅ Graphiti Wrapper:   localhost:5001"
echo "  ✅ Memory Proxy:       localhost:8000"
echo ""
echo "Configuration:"
echo "  📂 Project:    /Users/joaolucas/Desktop/Proxy Orchestrator/proxy-orchestrator"
echo "  👤 User ID:    lucas-ai (shared memory)"
echo "  🧠 Tiers:      3-tier progressive injection"
echo ""
echo "Usage in Msty:"
echo "  API Endpoint: http://localhost:8000"
echo "  API Key:      Your OpenAI API key"
echo ""
echo "Monitor logs:"
echo "  Proxy:    tail -f /tmp/proxy_v3.log"
echo "  Graphiti: tail -f /tmp/http_wrapper.log"
echo "  Redis:    redis-cli INFO"
echo ""
echo "Test connection:"
echo "  curl http://localhost:8000/health"
echo ""
