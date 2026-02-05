.PHONY: help install run dev clean test format code-scout refactoring-agent schema-validator code-formatter servers ngrok

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Start all 4 MCP servers"
	@echo "  make ngrok      - Start all 4 MCP servers with ngrok tunnels"
	@echo "  make dev        - Start all 4 MCP servers (watch mode not required)"
	@echo "  make code-scout        - Start Code Scout MCP server standalone (port 1338)"
	@echo "  make refactoring-agent - Start Refactoring Agent MCP server standalone (port 1337)"
	@echo "  make schema-validator  - Start Schema Validator MCP server standalone (port 1340)"
	@echo "  make code-formatter    - Start Code Formatter MCP server standalone (stdio)"
	@echo "  make servers    - Show how to start servers individually"
	@echo "  make clean      - Clean cache and temp files"
	@echo "  make test       - Run tests"
	@echo "  make format     - Format code"

install:
	uv pip install -e .

run:
	./start.sh

dev:
	./start.sh

ngrok:
	@echo "🌐 Starting all MCP servers with ngrok tunnels..."
	./start_agents_ngrok.sh

code-scout:
	@echo "🔍 Starting Code Scout MCP Server on port 1338..."
	@if lsof -i:1338 >/dev/null 2>&1; then \
		echo "⚠️  Port 1338 already in use. Stop the existing process first."; \
		exit 1; \
	fi
	uv run python -m mcp_servers.code_scout.server

refactoring-agent:
	@echo "🔧 Starting Refactoring Agent MCP Server on port 1337..."
	@if lsof -i:1337 >/dev/null 2>&1; then \
		echo "⚠️  Port 1337 already in use. Stop the existing process first."; \
		exit 1; \
	fi
	PYTHONPATH="$$PWD:$$PYTHONPATH" uv run python mcp_servers/refactoring-agent/main.py

schema-validator:
	@echo "✔️  Starting Schema Validator Streamable-HTTP MCP Server on port 1340..."
	@if lsof -i:1340 >/dev/null 2>&1; then \
		echo "⚠️  Port 1340 already in use. Stop the existing process first."; \
		exit 1; \
	fi
	uv run python mcp_servers/schema-validator/main.py

code-formatter:
	@echo "📝 Starting Code Formatter MCP Server (Stdio)..."
	@echo "⚠️  Note: This server must be added via Chainlit UI to use"
	uv run python mcp_servers/code-formatter/main.py

servers:
	@echo "Starting individual MCP servers:"
	@echo ""
	@echo "Run in separate terminals using make commands:"
	@echo "  make code-scout"
	@echo "  make refactoring-agent"
	@echo "  make schema-validator"
	@echo "  make code-formatter"
	@echo ""
	@echo "Or run directly:"
	@echo "Code Scout (SSE, port 1338):"
	@echo "  python mcp_servers/code-scout/server.py"
	@echo ""
	@echo "Refactoring Agent (SSE, port 1337):"
	@echo "  python mcp_servers/refactoring-agent/main.py"
	@echo ""
	@echo "Schema Validator (Streamable-HTTP, port 1340):"
	@echo "  python mcp_servers/schema-validator/main.py"
	@echo ""
	@echo "Code Formatter (Stdio):"
	@echo "  uv run python mcp_servers/code-formatter/main.py"
	@echo ""
	@echo "Note: All servers must be added via Chainlit UI to use"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/

test:
	pytest

format:
	black .
	ruff check --fix .
