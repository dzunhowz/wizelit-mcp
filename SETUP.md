# Wizelit MCP Setup (MCP-only)

This repo ships 4 MCP servers with different transport modes (no Chainlit UI). Point the Wizelit UI to these endpoints and it will discover the available tools.

## Prerequisites

- Python 3.12+
- AWS credentials for Bedrock
- Redis (optional, for refactoring log streaming)

## Install

```bash
uv pip install -e .
```

## Configure

```bash
cp .env.template .env
# Fill in AWS and optional settings
```

Key env vars:

- Required: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `CHAT_MODEL_ID`
- Optional: `GITHUB_TOKEN`, `REDIS_URL`, `ENABLE_LOG_STREAMING`, `CREWAI_MODEL`, `CREWAI_TIMEOUT_SECONDS`, `JOB_LOG_TAIL`

## Run

Start all 4 servers together:

```bash
./start.sh
```

Or run manually in separate terminals:

```bash
# Terminal 1 - Code Scout (SSE, port 1338)
python mcp_servers/code-scout/server.py

# Terminal 2 - Refactoring Agent (SSE, port 1337)
python mcp_servers/refactoring-agent/main.py

# Terminal 3 - Schema Validator (Streamable-HTTP, port 1340)
python mcp_servers/schema-validator/main.py

# Terminal 4 - Code Formatter (Stdio)
# Note: This must be added via Chainlit UI, not run standalone
uv run python mcp_servers/code-formatter/main.py
```

Stop stale processes/ports:

```bash
./cleanup.sh
```

## Integration

**All MCP servers must be added via Chainlit UI** - there is no auto-discovery. Configure each server in Chainlit's MCP settings:

### Adding Servers via Chainlit UI

#### 1. Refactoring Agent (SSE)
- **Name**: `CodeRefactorAgent` (or your preferred name)
- **Type**: `SSE`
- **URL**: `http://127.0.0.1:1337/sse`

#### 2. Code Scout (SSE)
- **Name**: `CodeScoutAgent` (or your preferred name)
- **Type**: `SSE`
- **URL**: `http://127.0.0.1:1338/sse`

#### 3. Schema Validator (Streamable-HTTP)
- **Name**: `SchemaValidator` (or your preferred name)
- **Type**: `Streamable-HTTP`
- **URL**: `http://127.0.0.1:1340/mcp`

#### 4. Code Formatter (Stdio)
- **Name**: `CodeFormatterAgent` (or your preferred name)
- **Type**: `Stdio`
- **Command**: `uv`
- **Arguments**: `run python mcp_servers/code-formatter/main.py`
- **Working Directory**: `/path/to/sample-mcp-servers` (absolute path to this directory)

**Note**: Make sure the servers are running (via `./start.sh` or individually) before adding them in Chainlit UI.

## Dev Commands

- `make install` — install deps
- `make run` — start all 4 MCP servers
- `make servers` — show individual server commands
- `make clean` — clear caches
- `make test` — run tests
- `make format` — format with black + ruff

## Troubleshooting

- Ports busy: run `./cleanup.sh`
- Missing deps: `uv pip install -e .`
- Bedrock auth errors: re-check AWS env vars and region

---

Happy shipping! 🚀
