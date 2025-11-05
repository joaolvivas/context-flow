#!/bin/bash
# Stop all proxy services

echo "🛑 Stopping services..."

# Kill by port
lsof -ti:5001 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✓ Stopped HTTP Bridge (port 5001)" || echo "  • HTTP Bridge not running"
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✓ Stopped Memory Proxy (port 8000)" || echo "  • Memory Proxy not running"

# Kill by PID files if they exist
if [ -f "bridge.pid" ]; then
    kill -9 $(cat bridge.pid) 2>/dev/null && rm bridge.pid
fi

if [ -f "python-proxy/proxy.pid" ]; then
    kill -9 $(cat python-proxy/proxy.pid) 2>/dev/null && rm python-proxy/proxy.pid
fi

echo "✅ Done"
