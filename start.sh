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

# Start Code Scout MCP Server (port 1338)
if check_port 1338; then
    echo "⚠️  Port 1338 already in use (Code Scout might be running)"
else
    echo "🔍 Starting Code Scout MCP Server (port 1338)..."
    uv run python mcp_servers/code-scout/server.py &
    CODE_SCOUT_PID=$!
    echo "✅ Code Scout PID: $CODE_SCOUT_PID"
fi

# Start Refactoring Agent MCP Server (port 1337)
if check_port 1337; then
    echo "⚠️  Port 1337 already in use (Refactoring Agent might be running)"
else
    echo "🔧 Starting Refactoring Agent MCP Server (port 1337)..."
    uv run python mcp_servers/refactoring-agent/main.py &
    REFACTOR_PID=$!
    echo "✅ Refactoring Agent PID: $REFACTOR_PID"
fi

# Wait a bit for servers to start
echo ""
echo "⏳ Waiting for MCP servers to initialize..."
sleep 3

# Cleanup on exit
trap 'echo ""; echo "🛑 Shutting down..."; kill ${CODE_SCOUT_PID:-} ${REFACTOR_PID:-} 2>/dev/null; exit' INT TERM
