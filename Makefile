.PHONY: help install run dev clean test format

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Start all 4 MCP servers"
	@echo "  make dev        - Start all 4 MCP servers (watch mode not required)"
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

servers:
	@echo "Starting individual MCP servers:"
	@echo ""
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
