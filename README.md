# Wizelit MCP

FastMCP bundle exposing two MCP servers for the Wizelit UI. No UI is shipped here—this repo only runs the servers that Wizelit connects to.

- **Code Scout**: Fast code analysis (symbol usage, grep, dependency graph)
- **Refactoring Agent**: Background refactoring jobs with optional log streaming

## Architecture

```
wizelit-mcp/
├── mcp_servers/
│   ├── code-scout/          # Code Scout MCP server (port 1338, SSE)
│   │   ├── server.py
│   │   ├── scanner.py
│   │   ├── github_helper.py
│   │   └── github_cache.py
│   └── refactoring-agent/   # Refactoring MCP server (port 1337, SSE)
│       └── main.py
└── utils/
    └── bedrock_config.py    # AWS Bedrock configuration helpers
```

## Prerequisites

- Python 3.12+
- AWS credentials for Bedrock
- Redis (optional, for refactoring log streaming)
- PostgreSQL (optional, for job persistence via `DatabaseManager`)

## Setup

1. **Install dependencies**

   ```bash
   uv pip install -e .
   ```

2. **Configure environment**

   ```bash
   cp .env.template .env
   # Edit .env with your credentials
   ```

3. **Start the MCP servers**

   ```bash
   ./start.sh           # starts both servers (ports 1337, 1338)
   ```

   Or start them manually in two terminals:

   ```bash
   python mcp_servers/code-scout/server.py          # port 1338
   python mcp_servers/refactoring-agent/main.py     # port 1337
   ```

## Integration Endpoints

- Refactoring Agent SSE: `http://127.0.0.1:1337/sse`
- Code Scout SSE: `http://127.0.0.1:1338/sse`

The Wizelit UI (in the `wizelit` repo) should connect to these endpoints using FastMCP.

## Environment Variables

### Required

- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (default: `us-east-1`)
- `CHAT_MODEL_ID` (default: `anthropic.claude-3-haiku-20240307-v1:0`)

### Optional

- `GITHUB_TOKEN`: access private repos
- `REDIS_URL`, `ENABLE_LOG_STREAMING`: streaming logs for refactoring jobs
- `CREWAI_MODEL`, `CREWAI_TIMEOUT_SECONDS`: override CrewAI execution settings
- `JOB_LOG_TAIL`: number of lines returned when tailing job logs

## Development

- Start servers: `make run`
- Install deps: `make install`
- Run tests: `pytest`
- Format: `black .` and `ruff check .`

## Troubleshooting

- Ports 1337/1338 busy: stop existing processes with `./cleanup.sh`
- Missing deps: run `uv pip install -e .`
- Bedrock auth issues: confirm AWS env vars and region

## License

[Add your license here]
