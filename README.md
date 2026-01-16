# Wizelit MCP

A minimal Wizelit project powered by **wizelit-sdk**, featuring two MCP servers integrated with Chainlit:

- **Code Scout**: Fast code analysis and symbol tracking
- **Refactoring Agent**: AI-powered code refactoring using CrewAI

## Architecture

```
wizelit-mcp/
├── main.py                  # Chainlit app entry point
├── agent.py                 # Agent runtime connecting to MCP servers
├── graph.py                 # LangGraph agent definition
├── database.py              # Optional database manager
├── code_scout/              # Code analysis module
│   ├── code_scout.py
│   ├── github_helper.py
│   └── github_cache.py
├── mcp_servers/
│   ├── code-scout/          # Code Scout MCP server
│   │   └── server.py
│   └── refactoring-agent/   # Refactoring MCP server
│       └── main.py
└── utils/
    └── bedrock_config.py    # AWS Bedrock configuration
```

## Prerequisites

- Python 3.12+
- AWS Credentials (for Bedrock)
- Redis (optional, for log streaming)
- PostgreSQL (optional, for persistence)

## Setup

1. **Install dependencies**:
   ```bash
   uv pip install -e .
   ```

2. **Configure environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your credentials
   ```

3. **Start MCP servers**:
   ```bash
   # Terminal 1 - Code Scout
   python mcp_servers/code-scout/server.py

   # Terminal 2 - Refactoring Agent
   python mcp_servers/refactoring-agent/main.py
   ```

4. **Run Chainlit app**:
   ```bash
   chainlit run main.py
   ```

## Environment Variables

### Required
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (default: us-east-1)
- `CHAT_MODEL_ID`: Bedrock model ID (default: anthropic.claude-3-haiku-20240307-v1:0)

### Optional
- `GITHUB_TOKEN`: GitHub token for private repos
- `REDIS_URL`: Redis URL for log streaming (default: redis://localhost:6379)
- `ENABLE_LOG_STREAMING`: Enable streaming logs (default: true)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`: PostgreSQL config

## Usage

### Code Analysis
Ask the AI to analyze code:
- "Find all usages of `MyClass` in https://github.com/owner/repo"
- "Search for 'TODO' in my project"
- "Analyze the impact of changing function `process_data`"

### Code Refactoring
Ask the AI to refactor code:
- "Refactor this code to use type hints: [paste code]"
- "Improve this function's error handling: [paste code]"
- "Rewrite this using Pydantic models: [paste code]"

## Key Features

- **Unified Interface**: Single Chainlit chat interface for both analysis and refactoring
- **Real-time Streaming**: Watch refactoring jobs in real-time via Redis
- **GitHub Integration**: Analyze GitHub repositories directly
- **AWS Bedrock**: Powered by Claude models via AWS Bedrock
- **MCP Architecture**: Modular server architecture using Model Context Protocol

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
ruff check .
```

## License

[Add your license here]
