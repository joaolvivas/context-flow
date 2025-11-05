#!/bin/bash
# Startup script for Proxy Orchestrator + Graphiti HTTP Bridge

set -e

echo "🚀 Starting Proxy Orchestrator with Graphiti Memory..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f "python-proxy/.env" ]; then
    echo "⚠️  python-proxy/.env not found. Copying from .env.example..."
    cp python-proxy/.env.example python-proxy/.env
    echo "✏️  Please edit python-proxy/.env with your settings"
    exit 1
fi

# Function to start HTTP Bridge
start_bridge() {
    echo -e "${BLUE}Starting HTTP Bridge (Port 5000)...${NC}"
    cd "$(dirname "$0")"
    
    # Use existing Graphiti venv
    if [ -f "/Users/joaolucas/graphiti/mcp_server/.venv/bin/activate" ]; then
        source /Users/joaolucas/graphiti/mcp_server/.venv/bin/activate
    else
        echo "⚠️  Graphiti venv not found at /Users/joaolucas/graphiti/mcp_server/.venv"
        echo "Creating new venv..."
        python3 -m venv venv_bridge
        source venv_bridge/bin/activate
        pip install fastapi uvicorn neo4j python-dotenv graphiti-core pydantic
    fi
    
    python graphiti_http_bridge.py &
    BRIDGE_PID=$!
    echo -e "${GREEN}✓ HTTP Bridge started (PID: $BRIDGE_PID)${NC}"
}

# Function to start Memory Proxy
start_proxy() {
    echo -e "${BLUE}Starting Memory Proxy (Port 8000)...${NC}"
    cd "$(dirname "$0")/python-proxy"
    
    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo "Creating venv..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    
    python main.py &
    PROXY_PID=$!
    echo -e "${GREEN}✓ Memory Proxy started (PID: $PROXY_PID)${NC}"
}

# Trap Ctrl+C and cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    if [ ! -z "$BRIDGE_PID" ]; then
        kill $BRIDGE_PID 2>/dev/null || true
    fi
    if [ ! -z "$PROXY_PID" ]; then
        kill $PROXY_PID 2>/dev/null || true
    fi
    echo "👋 Bye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start services
start_bridge
sleep 3  # Wait for bridge to start

start_proxy
sleep 2  # Wait for proxy to start

echo ""
echo -e "${GREEN}✅ Both services started!${NC}"
echo ""
echo "Endpoints:"
echo "  - HTTP Bridge: http://localhost:5000"
echo "  - Memory Proxy: http://localhost:8000"
echo ""
echo "Test with:"
echo "  curl http://localhost:5000/health"
echo "  curl http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for background processes
wait
