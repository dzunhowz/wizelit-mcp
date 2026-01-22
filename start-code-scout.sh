#!/bin/bash

# Code Scout MCP Server - Standalone Start Script
# Starts the Code Scout MCP server on port 1338

set -e

echo "🔍 Starting Code Scout MCP Server..."
echo ""

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    if [ -f .env.template ]; then
        cp .env.template .env
        echo "✅ Created .env file. Please edit it with your credentials."
    else
        echo "⚠️  No .env.template found. Proceeding without .env..."
    fi
    echo ""
fi

# Function to check if a port is in use
check_port() {
    lsof -i:$1 >/dev/null 2>&1
}

# Check if port 1338 is already in use
if check_port 1338; then
    echo "⚠️  Port 1338 already in use. Please stop the existing process first."
    echo ""
    echo "To find and kill the process:"
    echo "  lsof -i:1338"
    echo "  kill -9 <PID>"
    exit 1
fi

echo "🚀 Starting Code Scout MCP Server on port 1338..."
uv run python mcp_servers/code-scout/server.py

# Note: No background mode - runs in foreground
# Press Ctrl+C to stop the server
