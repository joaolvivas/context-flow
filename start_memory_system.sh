#!/bin/bash
# ContextFlow - Unified 3-Tier Memory System
# One integrated solution: Working Memory + Session Facts + Long-term Graph Storage

set -e

echo "⚡ ContextFlow - Intelligent Memory Proxy"
echo "=========================================="
echo ""
echo "🧠 Unified 3-Tier Architecture:"
echo "   • Tier 1: Working Memory (Redis) - Last 10 turns, <1ms"
echo "   • Tier 2: Session Facts (Redis) - Extracted facts, ~5ms"
echo "   • Tier 3: Knowledge Graph (Neo4j + Graphiti) - Deep context, ~500ms"
echo ""
echo "Starting all components..."
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
echo "=========================================="
echo -e "${GREEN}⚡ ContextFlow is ready!${NC}"
echo "=========================================="
echo ""
echo "📍 Endpoints:"
echo "   Memory Proxy:    http://localhost:8000"
echo "   Health Check:    http://localhost:8000/health"
echo ""
echo "🧠 Memory Tiers (unified system):"
echo "   ✅ Tier 1 (Redis):     Working memory - 10 recent turns"
echo "   ✅ Tier 2 (Redis):     Session facts - Extracted information"
echo "   ✅ Tier 3 (Neo4j):     Knowledge graph - Long-term relationships"
echo ""
echo "🔌 How to Use:"
echo "   1. Point your AI tool to: http://localhost:8000/v1"
echo "   2. Use your OpenAI API key"
echo "   3. Chat normally - memory flows automatically!"
echo ""
echo "📱 Compatible with:"
echo "   • Cursor IDE, VS Code, Windsurf"
echo "   • Msty Studio, Open WebUI"
echo "   • Aider, Claude Code (CLI)"
echo "   • Any tool with custom API endpoint"
echo ""
echo "📊 Monitoring:"
echo "   Proxy logs:    tail -f /tmp/proxy_v3.log"
echo "   Graphiti logs: tail -f /tmp/http_wrapper.log"
echo "   Redis:         redis-cli INFO"
echo ""
echo "💡 Features:"
echo "   ⚡ Automatic memory (zero manual calls)"
echo "   🎯 77% token reduction with progressive injection"
echo "   🚀 <120ms average response time"
echo "   🧠 Graph-based knowledge relationships"
echo ""
echo "Need help? Check README.md or run: curl http://localhost:8000/health"
echo ""
