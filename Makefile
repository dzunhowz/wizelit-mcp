.PHONY: help install run dev clean test format code-scout refactoring-agent servers

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make run               - Start both MCP servers"
	@echo "  make dev               - Start both MCP servers (watch mode not required)"
	@echo "  make code-scout        - Start Code Scout MCP server standalone (port 1338)"
	@echo "  make refactoring-agent - Start Refactoring Agent MCP server standalone (port 1337)"
	@echo "  make servers           - Show commands to start servers in separate terminals"
	@echo "  make clean             - Clean cache and temp files"
	@echo "  make test              - Run tests"
	@echo "  make format            - Format code"

install:
	uv pip install -e .

run:
	./start.sh

dev:
	./start.sh

code-scout:
	@echo "🔍 Starting Code Scout MCP Server on port 1338..."
	@if lsof -i:1338 >/dev/null 2>&1; then \
		echo "⚠️  Port 1338 already in use. Stop the existing process first."; \
		exit 1; \
	fi
	uv run python mcp_servers/code-scout/server.py

refactoring-agent:
	@echo "🔧 Starting Refactoring Agent MCP Server on port 1337..."
	@if lsof -i:1337 >/dev/null 2>&1; then \
		echo "⚠️  Port 1337 already in use. Stop the existing process first."; \
		exit 1; \
	fi
	PYTHONPATH="$$PWD:$$PYTHONPATH" uv run python mcp_servers/refactoring-agent/main.py

servers:
	@echo "Starting MCP servers..."
	@echo "Run in separate terminals:"
	@echo "  make code-scout"
	@echo "  make refactoring-agent"
	@echo ""
	@echo "Or directly:"
	@echo "  python mcp_servers/code-scout/server.py"
	@echo "  python mcp_servers/refactoring-agent/main.py"

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
