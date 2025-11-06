#!/bin/bash
# ContextFlow Memory System - Unified Startup Script
# Use: bash start_memory_system.sh

set -e

PROJECT_DIR="/Users/joaolucas/Desktop/Proxy Orchestrator/proxy-orchestrator"
MCP_DIR="/Users/joaolucas/graphiti/mcp_server"

echo "🚀 Starting ContextFlow Memory System"
echo "======================================"
echo ""

# Kill existing processes
echo "🛑 Stopping existing services..."
pkill -9 -f "main.py|graphiti_http_bridge" 2>/dev/null || true
sleep 2

# Start Graphiti HTTP Bridge (Port 5001)
echo "📡 Starting Graphiti Bridge (Port 5001)..."
cd "$PROJECT_DIR"
source "$MCP_DIR/.venv/bin/activate"
MCP_PORT=5001 python src/contextflow/bridges/graphiti_http_bridge.py > /tmp/http_wrapper.log 2>&1 &
BRIDGE_PID=$!
echo "   ✓ Bridge started (PID: $BRIDGE_PID)"

# Wait for bridge to be ready
sleep 3

# Start Memory Proxy (Port 8000)
echo "🧠 Starting Memory Proxy (Port 8000)..."
cd "$PROJECT_DIR/python-proxy"
source venv/bin/activate
python main.py > /tmp/proxy_v3.log 2>&1 &
PROXY_PID=$!
echo "   ✓ Proxy started (PID: $PROXY_PID)"

# Wait for services to initialize
sleep 5

echo ""
echo "======================================"
echo "✅ ContextFlow Memory System is RUNNING!"
echo "======================================"
echo ""
echo "Services:"
echo "  🧠 Memory Proxy:    http://localhost:8000"
echo "  📡 Graphiti Bridge: http://localhost:5001"
echo ""
echo "Health checks:"
curl -s http://localhost:8000/health | jq -r '"  Proxy: \(.status) (v\(.version))"' 2>/dev/null || echo "  Proxy: checking..."
curl -s http://localhost:5001/health | jq -r '"  Bridge: \(.status)"' 2>/dev/null || echo "  Bridge: checking..."
echo ""
echo "Logs:"
echo "  📝 Proxy:  tail -f /tmp/proxy_v3.log"
echo "  📝 Bridge: tail -f /tmp/http_wrapper.log"
echo ""
echo "To stop: pkill -f 'main.py|graphiti_http_bridge'"
echo ""
echo "$PROXY_PID" > /tmp/contextflow_proxy.pid
echo "$BRIDGE_PID" > /tmp/contextflow_bridge.pid
