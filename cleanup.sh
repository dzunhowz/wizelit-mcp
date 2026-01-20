#!/bin/bash

# Cleanup Script for Wizelit MCP
# Kills stale MCP server processes

echo "🧹 Cleaning up stale processes..."
echo ""

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    local name=$2
    
    pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "🔴 Killing $name on port $port (PIDs: $pids)"
        kill $pids 2>/dev/null || kill -9 $pids 2>/dev/null
        sleep 1
    else
        echo "✅ Port $port is free ($name)"
    fi
}

# Function to kill processes by name pattern
kill_by_name() {
    local pattern=$1
    local name=$2
    
    pids=$(ps -ef | grep "$pattern" | grep -v grep | awk '{print $2}')
    if [ -n "$pids" ]; then
        echo "🔴 Killing $name processes (PIDs: $pids)"
        kill $pids 2>/dev/null || kill -9 $pids 2>/dev/null
        sleep 1
    else
        echo "✅ No $name processes found"
    fi
}

echo "Checking ports:"
echo "---------------"
kill_port 1337 "Refactoring Agent"
kill_port 1338 "Code Scout"

echo ""
echo "Checking process names:"
echo "------------------------"
kill_by_name "mcp_servers/code-scout/server.py" "Code Scout"
kill_by_name "mcp_servers/refactoring-agent/main.py" "Refactoring Agent"

echo ""
echo "✨ Cleanup complete!"
echo ""
echo "Verify all ports are free:"
lsof -i:1337 -i:1338 2>/dev/null || echo "  ✅ All ports (1337, 1338) are free"
