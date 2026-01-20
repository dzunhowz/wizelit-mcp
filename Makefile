.PHONY: help install run dev clean test format

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Start both MCP servers"
	@echo "  make dev        - Start both MCP servers (watch mode not required)"
	@echo "  make servers    - Start all MCP servers"
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
	@echo "Starting MCP servers..."
	@echo "Run in separate terminals:"
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
