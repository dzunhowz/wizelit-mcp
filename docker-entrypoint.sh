#!/bin/bash
# =============================================================================
# Wizelit MCP Servers - Docker Entrypoint
# Starts the MCP server with a reverse proxy to handle ALB path prefixes.
#
# Problem: ALB routes /code-scout/sse → container, but server only handles /sse
# Solution: Proxy strips path prefix before forwarding to MCP server
#
# Flow:
#   ALB → Port 1338 (proxy) → Port 9000 (MCP server)
#   /code-scout/sse → /sse
# =============================================================================

set -e

echo "Starting Wizelit MCP Server: ${MCP_SERVER:-code-scout}"

# Internal port for MCP server (proxy will forward to this)
INTERNAL_PORT=9000

# Cleanup function
cleanup() {
    echo "Shutting down..."
    if [ -n "$MCP_PID" ] && kill -0 $MCP_PID 2>/dev/null; then
        kill $MCP_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup INT TERM

case "${MCP_SERVER}" in
    "code-scout")
        echo "🔍 Starting Code Scout (SSE, external port 1338)..."
        export MCP_PORT=1338
        export MCP_SERVER_PORT=$INTERNAL_PORT
        export BACKEND_PORT=$INTERNAL_PORT
        export PROXY_PORT=$MCP_PORT
        
        # Start MCP server on internal port in background
        cd /app/mcp_servers/code-scout
        python server.py &
        MCP_PID=$!
        ;;
    "refactoring-agent")
        echo "🔧 Starting Refactoring Agent (SSE, external port 1337)..."
        export MCP_PORT=1337
        export MCP_SERVER_PORT=$INTERNAL_PORT
        export BACKEND_PORT=$INTERNAL_PORT
        export PROXY_PORT=$MCP_PORT
        export PYTHONPATH="/app:$PYTHONPATH"
        
        # Start MCP server on internal port in background
        python /app/mcp_servers/refactoring-agent/main.py &
        MCP_PID=$!
        ;;
    "schema-validator")
        echo "✔️ Starting Schema Validator (Streamable-HTTP, external port 1340)..."
        export MCP_PORT=1340
        export MCP_SERVER_PORT=$INTERNAL_PORT
        export BACKEND_PORT=$INTERNAL_PORT
        export PROXY_PORT=$MCP_PORT
        
        # Start MCP server on internal port in background
        python /app/mcp_servers/schema-validator/main.py &
        MCP_PID=$!
        ;;
    *)
        echo "❌ Unknown MCP_SERVER: ${MCP_SERVER}"
        echo "   Valid options: code-scout, refactoring-agent, schema-validator"
        exit 1
        ;;
esac

# Wait for MCP server to start
echo "⏳ Waiting for MCP server to start on internal port $INTERNAL_PORT..."
MAX_WAIT=30
WAITED=0
while ! nc -z 127.0.0.1 $INTERNAL_PORT 2>/dev/null; do
    sleep 1
    WAITED=$((WAITED + 1))
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "❌ MCP server failed to start within $MAX_WAIT seconds"
        # Check if process is still running
        if ! kill -0 $MCP_PID 2>/dev/null; then
            echo "❌ MCP server process died"
        fi
        exit 1
    fi
    echo "   Still waiting... ($WAITED/$MAX_WAIT)"
done

echo "✅ MCP server started (PID: $MCP_PID) on port $INTERNAL_PORT"

# Start the reverse proxy (this will be the main process)
echo "🌐 Starting reverse proxy: port $PROXY_PORT → internal port $BACKEND_PORT"
exec python /app/path_proxy.py
