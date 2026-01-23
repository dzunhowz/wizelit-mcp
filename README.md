# Wizelit Sample MCP Servers

FastMCP bundle exposing 4 sample MCP servers to test multiple transport modes for the Wizelit Platform.

## Agents (4 Transport Examples)

| Agent | Transport | Port | Purpose | Status |
|-------|-----------|------|---------|--------|
| **Code Scout** | SSE | 1338 | Fast code analysis | ✅ Existing |
| **Refactoring Agent** | SSE | 1337 | Background refactoring jobs | ✅ Existing |
| **Schema Validator** | Streamable-HTTP | 1340 | Code structure validation | ✅ Active |
| **Code Formatter** | Stdio | N/A | Code formatting (local) | ✅ Active |

## Architecture

```
sample-mcp-servers/
├── mcp_servers/
│   ├── code-scout/           # Code Scout (SSE, port 1338)
│   │   ├── server.py
│   │   ├── scanner.py
│   │   ├── github_helper.py
│   │   └── github_cache.py
│   ├── refactoring-agent/    # Refactoring Crew (SSE, port 1337)
│   │   └── main.py
│   ├── schema-validator/     # Schema Validator (Streamable-HTTP, port 1340)
│   │   ├── main.py
│   │   └── validator.py
│   └── code-formatter/       # Code Formatter (Stdio)
│       ├── main.py
│       └── formatter.py
├── utils/
│   └── bedrock_config.py     # AWS Bedrock configuration
├── TRANSPORT_GUIDE.md        # 🆕 Transport modes explained
└── SETUP.md                  # Setup instructions
```

## Quick Start

### 1. Install Dependencies
```bash
uv pip install -e .
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env with your AWS credentials
```

### 3. Start All Servers
```bash
./start.sh
```

This starts all 4 agents:
- Code Scout (SSE, :1338)
- Refactoring Agent (SSE, :1337)  
- Schema Validator (Streamable-HTTP, :1340)
- Code Formatter (Stdio)

### 4. Or Start Individually

**Terminal 1** - Code Scout (SSE):
```bash
python mcp_servers/code-scout/server.py
```

**Terminal 2** - Refactoring Agent (SSE):
```bash
python mcp_servers/refactoring-agent/main.py
```

**Terminal 3** - Schema Validator (Streamable-HTTP):
```bash
python mcp_servers/schema-validator/main.py
```

**Terminal 4** - Code Formatter (Stdio):
```bash
python mcp_servers/code-formatter/main.py
```

## Integration Endpoints

- **Refactoring Agent SSE**: `http://127.0.0.1:1337/sse`
- **Code Scout SSE**: `http://127.0.0.1:1338/sse`
- **Schema Validator Streamable-HTTP**: `http://127.0.0.1:1340/mcp` (POST-based)
- **Code Formatter**: Stdio-based (process-based)

**Important**: All MCP servers must be manually added via Chainlit UI - there is no auto-discovery. See SETUP.md for detailed configuration instructions for each server.

## Troubleshooting

**Port already in use**: Run `./cleanup.sh` to kill any stale processes
```bash
./cleanup.sh
```

**Missing dependencies**: Install with:
```bash
uv pip install -e .
```

**Bedrock auth errors**: Check AWS environment variables:
```bash
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
echo $AWS_DEFAULT_REGION
```

| Agent | Endpoint | Transport |
|-------|----------|-----------|
| Refactoring Agent | `http://127.0.0.1:1337/sse` | SSE |
| Code Scout | `http://127.0.0.1:1338/sse` | SSE |
| Schema Validator | `http://127.0.0.1:1340/mcp` | Streamable-HTTP |
| Code Formatter | Process-based stdin/stdout | Stdio |

The Wizelit Platform should connect to these endpoints and discover available tools.

## Transport Modes Explained

See [TRANSPORT_GUIDE.md](TRANSPORT_GUIDE.md) for detailed information about:
- **SSE (Server-Sent Events)** - Long-running with streaming
- **Streamable-HTTP** - Standard request-response
- **Stdio** - Local process execution

## Environment Variables

### Required (for Refactoring Agent only)

- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (default: `us-east-1`)
- `CHAT_MODEL_ID` (default: `anthropic.claude-3-haiku-20240307-v1:0`)

### Optional

- `GITHUB_TOKEN`: access private repos (Code Scout)
- `REDIS_URL`, `ENABLE_LOG_STREAMING`: log streaming (Refactoring Agent)
- `CREWAI_MODEL`, `CREWAI_TIMEOUT_SECONDS`: CrewAI settings
- `JOB_LOG_TAIL`: log lines to return (default: 25)

## Development

```bash
# Install dependencies
make install

# Start all servers
make run

# Show individual server commands
make servers

# Format code
make format

# Clean cache
make clean
```

## Agent Examples

### Schema Validator (Fast, Request-Response)
Validates Python function/class signatures:
```bash
curl -X POST http://127.0.0.1:1340/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "validate_function_signature",
    "params": {
      "code": "def greet(name: str) -> str: return f\"Hello, {name}!\"",
      "function_name": "greet",
      "expected_params": "[\"name\"]",
      "expected_return_type": "str"
    }
  }'
```

### Code Formatter (Stdio, Local)
Formats Python code. **Note**: All servers must be added via Chainlit UI. Code Formatter uses stdio transport and cannot be tested directly with curl.

To use:
1. Add all servers via Chainlit UI (see SETUP.md for details)
2. Use the tools through the Wizelit Platform interface

Available Code Formatter tools:
- `format_code` - Apply Black-style formatting rules
- `organize_imports` - Organize and sort import statements
- `normalize_indentation` - Normalize indentation (default: 4 spaces)
- `format_all` - Apply all formatting rules in sequence

## Troubleshooting

### Port Already in Use
```bash
# Kill existing processes
./cleanup.sh

# Or manually
lsof -i:1337  # Find process
kill -9 <PID>
```

### Agent Won't Start
```bash
# Check Python version
python --version  # Must be 3.10+

# Check dependencies
uv pip list | grep wizelit-sdk

# Run agent directly to see errors
python mcp_servers/schema-validator/main.py
```

### Platform Can't Connect
```bash
# Test HTTP endpoint
curl http://127.0.0.1:1340/mcp

# Check firewall
sudo lsof -i:1340

# Check logs
python -u mcp_servers/schema-validator/main.py  # With unbuffered output
```

## Key Files

| File | Purpose |
|------|---------|
| `TRANSPORT_GUIDE.md` | 🆕 Deep dive into transport modes |
| `SETUP.md` | Detailed setup instructions |
| `mcp_servers/schema-validator/` | 🆕 Example: Streamable-HTTP agent |
| `mcp_servers/code-formatter/` | 🆕 Example: Stdio agent |
| `start.sh` | 🆕 Updated to run all 4 agents |

## References

- [MCP Protocol](https://modelcontextprotocol.io)
- [FastMCP](https://github.com/jlouis/fastmcp)
- [Wizelit SDK](../../../SDK/wizelit-sdk)
- [Transport Comparison](TRANSPORT_GUIDE.md)

## License

[Add your license here]

