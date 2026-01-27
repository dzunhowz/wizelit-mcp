#!/bin/bash

# Wizelit MCP - Start Script
# This script starts the MCP servers (no UI)

set -e

echo "🚀 Starting Wizelit MCP servers..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.template .env
    echo "✅ Created .env file. Please edit it with your credentials."
    echo ""
fi

# Function to check if a port is in use
check_port() {
    lsof -i:$1 >/dev/null 2>&1
}

# Start Code Scout MCP Server (port 1338, SSE)
if check_port 1338; then
    echo "⚠️  Port 1338 already in use (Code Scout might be running)"
else
    echo "🔍 Starting Code Scout MCP Server (port 1338, SSE)..."
    uv run python -m mcp_servers.code_scout.server &
    CODE_SCOUT_PID=$!
    echo "✅ Code Scout PID: $CODE_SCOUT_PID"
fi

# Start Refactoring Agent MCP Server (port 1337, SSE)
if check_port 1337; then
    echo "⚠️  Port 1337 already in use (Refactoring Agent might be running)"
else
    echo "🔧 Starting Refactoring Agent MCP Server (port 1337, SSE)..."
    PYTHONPATH="$PWD:$PYTHONPATH" uv run python mcp_servers/refactoring-agent/main.py &
    REFACTOR_PID=$!
    echo "✅ Refactoring Agent PID: $REFACTOR_PID"
fi

# Start Schema Validator Streamable-HTTP MCP Server (port 1340)
if check_port 1340; then
    echo "⚠️  Port 1340 already in use (Schema Validator might be running)"
else
    echo "✔️  Starting Schema Validator Streamable-HTTP MCP Server (port 1340)..."
    uv run python mcp_servers/schema-validator/main.py &
    VALIDATOR_PID=$!
    echo "✅ Schema Validator Streamable-HTTP PID: $VALIDATOR_PID"
fi

# Start Code Formatter MCP Server (Stdio)
echo "📝 Starting Code Formatter MCP Server (Stdio)..."
uv run python mcp_servers/code-formatter/main.py &
FORMATTER_PID=$!
echo "✅ Code Formatter PID: $FORMATTER_PID"

# Wait a bit for servers to start
echo ""
echo "⏳ Waiting for MCP servers to initialize..."
sleep 3

# Print server info
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          🚀 Wizelit MCP Servers Running                 ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║ Code Scout (SSE)         → http://127.0.0.1:1338/sse   ║"
echo "║ Refactoring Agent (SSE)  → http://127.0.0.1:1337/sse   ║"
echo "║ Schema Validator (HTTP)  → http://127.0.0.1:1340/mcp   ║"
echo "║ Code Formatter (Stdio)   → Process-based               ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║ PIDs: $CODE_SCOUT_PID, $REFACTOR_PID, $VALIDATOR_PID, $FORMATTER_PID"
echo "║ Press Ctrl+C to stop all services"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Cleanup on exit
trap 'echo ""; echo "🛑 Shutting down..."; kill ${CODE_SCOUT_PID:-} ${REFACTOR_PID:-} ${VALIDATOR_PID:-} ${FORMATTER_PID:-} 2>/dev/null; exit' INT TERM

