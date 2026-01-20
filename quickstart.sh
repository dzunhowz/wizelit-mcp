#!/bin/bash

# Quick Start Guide for Wizelit MCP

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          Wizelit MCP - Quick Start Guide                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "Please create .env from template:"
    echo "  cp .env.template .env"
    echo ""
    echo "Then edit .env with your credentials:"
    echo "  - AWS_ACCESS_KEY_ID"
    echo "  - AWS_SECRET_ACCESS_KEY"
    echo "  - AWS_REGION"
    echo "  - CHAT_MODEL_ID"
    echo ""
    exit 1
fi

echo "✅ Environment file found"
echo ""

# Check if dependencies are installed
if ! uv run python -c "import wizelit_sdk" 2>/dev/null; then
    echo "❌ Dependencies not installed!"
    echo ""
    echo "Please install dependencies:"
    echo "  uv pip install -e ."
    echo "  or"
    echo "  make install"
    echo ""
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

echo "🚀 Starting Wizelit MCP servers..."
echo ""
echo "This will start:"
echo "  1. Code Scout MCP Server (port 1338)"
echo "  2. Refactoring Agent MCP Server (port 1337)"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""
echo "Starting in 3 seconds..."
sleep 3

./start.sh
