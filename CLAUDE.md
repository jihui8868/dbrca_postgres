# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**dbrca-postgres** is a multi-agent AI system for database root cause analysis (RCA), specifically designed for PostgreSQL diagnostics. It uses a hierarchical agent architecture where a main orchestrator agent delegates specialized tasks to sub-agents using the DeepAgents framework, powered by LLM (DeepSeek Chat by default).

### Key Components
- **Main Agent**: Orchestrates user intent → parses inputs → delegates to sub-agents
- **Sub-agents**: Specialized agents for data parsing, seismic interpretation, validation, and report generation
- **FastAPI Server**: REST API for agent interaction + offline Swagger/ReDoc documentation
- **CLI Mode**: Direct terminal interaction with agents (useful for development/testing)
- **Logging**: Structured logging with daily file rotation and colored console output

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Agent Framework**: DeepAgents (multi-agent orchestration)
- **LLM Integration**: LangChain OpenAI (compatible with DeepSeek, OpenAI, etc.)
- **Database**: PostgreSQL (psycopg) + SQLAlchemy ORM (configured, not yet active)
- **Dependency Management**: uv (Python 3.13+)

## Setup

### Prerequisites
- Python 3.13+ (specified in `.python-version`)
- PostgreSQL (configured in settings, but optional for initial development)

### Environment Configuration

Create a `.env` file in the project root. See `app/core/config.py` for the schema:

```env
# LLM Configuration
LLM__MODEL=deepseek-chat
LLM__BASE_URL=https://api.deepseek.com/v1
LLM__API_KEY=sk-your-api-key
LLM__TEMPERATURE=0.0
LLM__MAX_TOKENS=8192

# PostgreSQL Configuration (if using database features)
POSTGRES__HOST=127.0.0.1
POSTGRES__PORT=5432
POSTGRES__USER=postgres
POSTGRES__PASSWORD=your-password
POSTGRES__DATABASE=your-database
POSTGRES__ERROR_LOG_PATH=/var/log/postgresql/postgresql.log

# LangSmith Tracing (optional)
LANGSMITH__ENABLED=false
LANGSMITH__API_KEY=
LANGSMITH__PROJECT=dbrca-postgres

# Agent Configuration
AGENT__MAX_ITERATIONS=50
AGENT__SESSION_TTL_SECONDS=3600

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

### Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Running the Application

### FastAPI Server (Default)
```bash
# Start with default settings (0.0.0.0:7777)
python -m app.main

# Custom host/port
python -m app.main --host 0.0.0.0 --port 8080

# Access API:
# - OpenAPI Docs (Swagger): http://localhost:7777/docs
# - ReDoc: http://localhost:7777/redoc
# - Health check: http://localhost:7777/health
```

### CLI Mode (Terminal Interaction)
```bash
# Interactive REPL mode
python -m app.main --cli

# Single input (non-interactive)
python -m app.main --cli --input "Your query here"

# With debug output
python -m app.main --cli --debug

# Specific session ID
python -m app.main --cli --session my-session-id
```

## Project Structure

```
app/
├── main.py                 # FastAPI app creation and entry point
├── core/
│   ├── config.py          # Settings schema (LLM, DB, Agent, Log configs)
│   └── logging_config.py  # Logging system setup (colored console + daily file rotation)
├── agents/
│   ├── main_agent.py      # Main agent orchestrator (uses DeepAgents)
│   └── subagents/         # Sub-agent definitions (in development)
├── crud/                  # Database CRUD operations (placeholder)
├── models/                # SQLAlchemy models (placeholder)
├── routers/               # API route handlers (placeholder)
└── schemas/               # Pydantic request/response schemas (placeholder)

static/                    # Offline Swagger/ReDoc assets
  ├── swagger-ui-bundle.js
  ├── swagger-ui.css
  └── redoc.standalone.js
```

## Architecture Notes

### Main Agent System
The main agent (`build_main_agent()` in `app/agents/main_agent.py`) is built using `create_deep_agent()` from DeepAgents:

- **System Prompt**: Instructs the agent to understand user intent and delegate to sub-agents
- **Sub-agents**: Define specialized tasks (data_parse, data_explain, data_validate, report_gen)
- **Skills**: Optional external skill definitions (from settings.skills if available)
- **Logging**: Uses Python's logging module with correlation via `session_id`

Sub-agents are defined in `app/agents/subagents/` and aggregated in `ALL_SUBAGENTS` list.

### Configuration Pattern
All settings use Pydantic models with environment variable loading:
- Environment variables use `__` as nested delimiter (e.g., `LLM__API_KEY`)
- Configs are loaded via `get_settings()` with LRU cache
- Missing critical keys (like `api_key`) trigger warnings but don't crash startup

### Logging
Setup is idempotent (safe to call multiple times):
- **Console**: Colored output (INFO+), formatted with timestamp and logger name
- **File**: `logs/earthquake.log` with daily rotation (30-day retention)
- **Level**: DEBUG for file, configurable for console (default INFO)
- **Suppression**: Verbose libraries (httpx, httpcore, urllib3, openai) are silenced at WARNING level

## Development Workflow

### Adding Routes
1. Create endpoint in `app/routers/` (not yet active, commented in `main.py`)
2. Define request/response schemas in `app/schemas/`
3. Uncomment router in `main.py` and add to `include_router()`
4. Test via `/docs` OpenAPI interface or CLI mode

### Adding Sub-agents
1. Define agent spec in `app/agents/subagents/` (name, system_prompt, tools)
2. Add to `ALL_SUBAGENTS` list
3. Reference in main agent's system prompt
4. Test with CLI mode: `python -m app.main --cli --debug`

### Debugging
- Use `--cli --debug` mode to see detailed agent execution
- Check `logs/earthquake.log` for file-level debug output
- Set `LOG_LEVEL=DEBUG` in `.env` for console debug output
- LangSmith tracing can be enabled in `.env` for visual flow analysis

## Notes

- The project uses nested Pydantic models (`postgres`, `llm`, `agent`, `app` configs) all under a single `Settings` class loaded from `.env`
- FastAPI docs are served offline (not from CDN) for air-gapped environments
- CLI mode imports from `app.cli.agent_chat` (not yet present — will be created as needed)
- Database features (CRUD, models) are scaffolded but not yet connected
- Router mounts are commented out — uncomment as endpoints are developed
