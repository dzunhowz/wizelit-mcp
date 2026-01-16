# Wizelit MCP - Project Setup Complete! 🎉

## What Was Created

A new minimal project **`wizelit-mcp`** has been successfully created at:

```
/Users/dung.ho/Documents/Training/Python/wizelit-mcp
```

This project is a clean implementation that:

- ✅ Uses **wizelit-sdk** for all MCP wrapper functionality
- ✅ Includes only the 2 MCP servers (code-scout and refactoring-agent)
- ✅ Has minimal dependencies
- ✅ Integrates with Chainlit for the UI

## Project Structure

```
wizelit-mcp/
├── main.py                    # Chainlit app entry point
├── agent.py                   # Agent runtime (connects to MCP servers)
├── graph.py                   # LangGraph agent definition
├── database.py                # Optional database manager
├── pyproject.toml             # Dependencies
├── start.sh                   # Convenience startup script
├── Makefile                   # Development commands
├── README.md                  # Documentation
├── .env.template              # Environment template
├── .gitignore                 # Git ignore rules
├── chainlit.md                # Welcome message
│
├── code_scout/                # Code analysis module
│   ├── __init__.py
│   ├── code_scout.py          # Core analysis logic
│   ├── github_helper.py       # GitHub integration
│   └── github_cache.py        # Repository caching
│
├── mcp_servers/               # MCP Servers
│   ├── code-scout/
│   │   ├── server.py          # Code Scout MCP server (port 1338)
│   │   ├── README.md
│   │   └── __init__.py
│   └── refactoring-agent/
│       └── main.py            # Refactoring MCP server (port 1337)
│
├── utils/                     # Utilities
│   ├── __init__.py
│   └── bedrock_config.py      # AWS Bedrock configuration
│
├── .chainlit/                 # Chainlit configuration
│   └── config.toml
│
└── public/                    # Static assets (CSS, theme)
    ├── styles.css
    └── theme.json
```

## Key Dependencies

The project uses these main dependencies (defined in `pyproject.toml`):

### Core

- `chainlit>=2.9.3` - UI framework
- `wizelit-sdk` - MCP wrapper and utilities (from your SDK repo)

### LLM & Agents

- `langchain>=1.1.3` - LLM framework
- `langgraph>=1.0.4` - Agent workflow
- `langchain-aws>=1.1.0` - AWS Bedrock integration
- `langchain-mcp-adapters>=0.2.1` - MCP integration
- `crewai>=1.6.1` - Multi-agent system

### MCP & Communication

- `mcp>=1.23.3` - Model Context Protocol
- `uvicorn>=0.30.0` - ASGI server for MCP

### Integrations

- `boto3>=1.42.5` - AWS SDK
- `PyGithub>=2.4.0` - GitHub API
- `redis>=4.5.0` - Streaming support

## How to Use

### 1. Setup Environment

```bash
cd /Users/dung.ho/Documents/Training/Python/wizelit-mcp

# Copy and edit environment variables
cp .env.template .env
# Edit .env with your AWS credentials and other settings
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

### 3. Start the Application

#### Option A: Use the start script (easiest)

```bash
./start.sh
```

This will:

- Start Code Scout MCP server (port 1338)
- Start Refactoring Agent MCP server (port 1337)
- Start Chainlit app

#### Option B: Manual startup (for development)

```bash
# Terminal 1 - Code Scout
python mcp_servers/code-scout/server.py

# Terminal 2 - Refactoring Agent
python mcp_servers/refactoring-agent/main.py

# Terminal 3 - Chainlit
chainlit run main.py
```

#### Option C: Using Makefile

```bash
# Install dependencies
make install

# Run the app
make run

# Or run in watch mode (auto-reload)
make dev
```

## Environment Variables

### Required

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
CHAT_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

### Optional

```bash
# GitHub token for private repos
GITHUB_TOKEN=your_github_token

# Redis for log streaming
REDIS_URL=redis://localhost:6379
ENABLE_LOG_STREAMING=true

# PostgreSQL for persistence (optional)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=wizelit_mcp
```

## Usage Examples

Once running, you can interact with the Chainlit UI at `http://localhost:8000`

### Code Analysis Examples

- "Find all usages of `MyClass` in https://github.com/owner/repo"
- "Search for 'TODO' comments in /path/to/project"
- "Analyze the impact of changing function `process_data`"
- "Show me the dependency graph for symbol `DatabaseManager`"

### Code Refactoring Examples

- "Refactor this code to use type hints: [paste code]"
- "Improve this function's error handling: [paste code]"
- "Rewrite this using Pydantic models: [paste code]"

## Key Features

1. **Wizelit SDK Integration**: All MCP wrapper functionality comes from wizelit-sdk
2. **Dual MCP Servers**:
   - Code Scout for analysis (fast, synchronous)
   - Refactoring Agent for code changes (background jobs)
3. **Real-time Streaming**: Watch refactoring jobs in real-time via Redis
4. **GitHub Support**: Analyze repositories directly from GitHub URLs
5. **AWS Bedrock**: Powered by Claude models via AWS Bedrock
6. **Clean Architecture**: Minimal dependencies, clear separation of concerns

## Differences from Original Wizelit

This project is a **minimal clone** that:

- ❌ Does NOT include OpenSearch integration
- ❌ Does NOT include legacy models/utilities from wizelit
- ❌ Does NOT include extra UI components
- ✅ ONLY has the 2 MCP servers
- ✅ Uses wizelit-sdk for all agent wrapper functionality
- ✅ Has a clean, minimal structure

## Development Commands

```bash
# Install dependencies
make install

# Run app
make run

# Run in watch mode (auto-reload)
make dev

# Clean cache files
make clean

# Format code
make format

# Run tests
make test
```

## Next Steps

1. **Configure Environment**: Edit `.env` with your credentials
2. **Test the Setup**: Run `./start.sh` to start everything
3. **Try It Out**: Open `http://localhost:8000` and test the chat interface
4. **Customize**: Modify `main.py`, `graph.py`, or MCP servers as needed

## Troubleshooting

### MCP Servers Won't Start

- Check ports 1337 and 1338 are available
- Ensure wizelit-sdk is installed correctly
- Check AWS credentials are set

### Cannot Connect to MCP Servers

- Ensure both MCP servers are running before starting Chainlit
- Check logs for connection errors
- Verify ports in `agent.py` match the MCP server ports

### Import Errors

- Run `uv pip install -e .` to install all dependencies
- Check that wizelit-sdk is accessible (installed from GitHub)

## Support

For issues or questions:

1. Check the README.md
2. Review error logs
3. Verify all environment variables are set correctly

---

**Happy Coding! 🚀**
