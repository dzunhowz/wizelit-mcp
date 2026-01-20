# Wizelit MCP Setup (MCP-only)

This repo now ships only the two FastMCP servers (no Chainlit UI). Point the Wizelit UI to these endpoints and it will discover the available tools.

## Prerequisites

- Python 3.12+
- AWS credentials for Bedrock
- Redis (optional, for refactoring log streaming)
- PostgreSQL (optional, for job persistence)

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
- Optional: `GITHUB_TOKEN`, `REDIS_URL`, `ENABLE_LOG_STREAMING`, `LOG_STREAM_TIMEOUT_SECONDS`, `POSTGRES_*`, `CREWAI_MODEL`, `CREWAI_TIMEOUT_SECONDS`, `JOB_LOG_TAIL`

## Run

Start both servers together:

```bash
./start.sh
```

Or run manually in separate terminals:

```bash
python mcp_servers/code-scout/server.py          # port 1338 (SSE)
python mcp_servers/refactoring-agent/main.py     # port 1337 (SSE)
```

Stop stale processes/ports:

```bash
./cleanup.sh
```

## Integration

- Refactoring Agent SSE: `http://127.0.0.1:1337/sse`
- Code Scout SSE: `http://127.0.0.1:1338/sse`

The Wizelit UI (in the separate `wizelit` repo) should connect to these FastMCP endpoints.

## Dev Commands

- `make install` — install deps
- `make run` — start both MCP servers
- `make clean` — clear caches
- `make test` — run tests
- `make format` — format with black + ruff

## Troubleshooting

- Ports busy: run `./cleanup.sh`
- Missing deps: `uv pip install -e .`
- Bedrock auth errors: re-check AWS env vars and region

---

Happy shipping! 🚀
