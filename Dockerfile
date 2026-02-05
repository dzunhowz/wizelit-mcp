# =============================================================================
# Wizelit MCP Servers - Multi-Server Dockerfile
# Supports: code-scout, refactoring-agent, schema-validator
# 
# Usage:
#   docker build -t wizelit-mcp .
#   docker run -e MCP_SERVER=code-scout -p 1338:1338 wizelit-mcp
#   docker run -e MCP_SERVER=refactoring-agent -p 1337:1337 wizelit-mcp
#   docker run -e MCP_SERVER=schema-validator -p 1340:1340 wizelit-mcp
# =============================================================================

FROM python:3.12-slim

WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MCP_SERVER=code-scout

# Install system dependencies (git required for Code Scout to clone repos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with home directory (required for CrewAI)
RUN groupadd -r mcp && useradd -r -g mcp -m -d /home/mcp mcp

# Copy dependency file and install
COPY pyproject.toml ./

RUN pip install --upgrade pip && \
    pip install .

# Copy application code
COPY . .

# Create data and cache directories
# CrewAI requires ~/.local/share for ChromaDB storage
RUN mkdir -p /app/data && \
    mkdir -p /home/mcp/.local/share && \
    chown -R mcp:mcp /app && \
    chown -R mcp:mcp /home/mcp

USER mcp

# Expose all possible ports
EXPOSE 1337 1338 1340

# Health check - proxy returns 200 OK at root path
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -sf http://localhost:${MCP_PORT:-1338}/ --max-time 5 || exit 1

# Entrypoint script to start the correct server
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
