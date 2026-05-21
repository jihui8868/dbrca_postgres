# FastAPI Backend Deployment Guide

This document covers the deployment and configuration of the Postgres RCA FastAPI backend with multi-agent system integration.

## Project Structure

The FastAPI backend has been fully implemented with the following components:

### API Routes (9 endpoints)

**Agent API (`/api/agent`)**:
- `POST /api/agent/query` - Synchronous agent query
- `POST /api/agent/analyze` - Comprehensive analysis (logs + query plans + metrics)
- `POST /api/agent/diagnose` - Database diagnostic analysis
- `GET /api/agent/stream/{session_id}` - Streaming query responses
- `GET /api/agent/sessions` - List all active sessions
- `GET /api/agent/sessions/{session_id}` - Get specific session details
- `DELETE /api/agent/sessions/{session_id}` - Delete session
- `GET /api/agent/health` - Health check with agent status

**WebSocket Routes** (implemented in `app/api/websocket.py`):
- `WS /ws/analyze/{session_id}` - Real-time analysis streaming
- `WS /ws/chat/{session_id}` - Multi-turn conversation with history

### Implementation Status

✓ **Completed**:
- All REST API endpoints fully implemented and tested
- Parameter validation using Pydantic models
- Session management with in-memory storage
- Health check endpoint with agent status reporting
- WebSocket support for real-time streaming
- Server-Sent Events (SSE) for streaming responses
- API documentation generation via FastAPI's `/docs`
- Web UI client (`app/static/rca-client.html`)
- Comprehensive API Guide (`API_GUIDE.md`)

## Configuration

### Prerequisites

1. **Python Environment**:
   ```bash
   python --version  # Python 3.10+
   source .venv/bin/activate
   ```

2. **LLM Provider Setup** - Choose one:

   **Option A: DeepSeek (Recommended)**
   - Sign up: https://platform.deepseek.com
   - Get API key from dashboard
   - Set in `.env`:
     ```
     LLM__MODEL=deepseek-chat
     LLM__BASE_URL=https://api.deepseek.com/v1
     LLM__API_KEY=sk-your-deepseek-api-key
     ```

   **Option B: OpenAI**
   - Get API key from https://platform.openai.com/account/api-keys
   - Set in `.env`:
     ```
     LLM__MODEL=gpt-4
     LLM__BASE_URL=https://api.openai.com/v1
     LLM__API_KEY=sk-your-openai-api-key
     ```

3. **Database Configuration** (optional):
   ```
   POSTGRES__HOST=127.0.0.1
   POSTGRES__PORT=5432
   POSTGRES__USER=postgres
   POSTGRES__PASSWORD=your_password
   POSTGRES__DATABASE=postgres
   ```

### Environment Variables

See `.env` file for all configuration options. Key settings:

```bash
# LLM Configuration (REQUIRED)
LLM__API_KEY=sk-your-api-key  # Must be set for agent endpoints to work

# Server Configuration
AGENT__MAX_ITERATIONS=50      # Max agent reasoning steps
AGENT__SESSION_TTL_SECONDS=3600  # Session timeout

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

## Running the Server

### Development Mode

```bash
# Start FastAPI with auto-reload
python -m app.main

# Or specify port
python -m app.main --port 8000
```

### Production Mode

```bash
# Using gunicorn with uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:7777
```

### Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync

ENV PORT=7777
CMD ["python", "-m", "app.main", "--port", "$PORT"]
```

## Testing

### API Integration Tests

```bash
# Run full test suite
python test_api_integration.py

# Expected output: All tests pass if LLM API key is configured
```

### Manual Testing

**Using curl**:
```bash
# Health check (no LLM required)
curl http://localhost:7777/api/agent/health

# Query agent (requires valid LLM API key)
curl -X POST http://localhost:7777/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "分析Postgres连接错误"}'
```

**Using Web UI**:
- Open browser: http://localhost:7777
- Interactive UI with live testing of all endpoints

**Using Python Client**:
```python
import requests

client = requests.Session()
base_url = "http://localhost:7777"

# Health check
health = client.get(f"{base_url}/api/agent/health").json()
print(health)

# Query (requires valid LLM API key)
response = client.post(
    f"{base_url}/api/agent/query",
    json={"query": "分析日志错误"}
).json()
```

## API Documentation

### Swagger UI
- URL: `http://localhost:7777/docs`
- Interactive API explorer with request/response examples

### OpenAPI Schema
- URL: `http://localhost:7777/api/agent/openapi.json`
- Machine-readable API specification

### Written Documentation
- `API_GUIDE.md` - Comprehensive guide with examples
- Python, JavaScript, and curl examples
- WebSocket connection examples
- Best practices and error handling

## Monitoring and Debugging

### Health Endpoint

```bash
curl http://localhost:7777/api/agent/health
```

Response includes:
- Overall system status
- Session count
- Individual agent status (all should be "ready")
- Timestamp

### Session Management

```bash
# List active sessions
curl http://localhost:7777/api/agent/sessions

# Get specific session
curl http://localhost:7777/api/agent/sessions/{session_id}

# Clean up session
curl -X DELETE http://localhost:7777/api/agent/sessions/{session_id}
```

### Logging

Server logs are written to `logs/` directory (configurable via `LOG_DIR`).

```bash
# View logs
tail -f logs/app.log

# Change log level in .env: LOG_LEVEL=DEBUG for verbose output
```

## Troubleshooting

### API returns 401 Authentication Error

**Issue**: "Error code: 401 - Authentication Fails"

**Solution**: Update `LLM__API_KEY` in `.env` with valid API key
- For DeepSeek: Get from https://platform.deepseek.com
- For OpenAI: Get from https://platform.openai.com/account/api-keys

### API returns 500 Internal Server Error

**Check**:
1. Server is running and listening on correct port
2. LLM API key is valid and not expired
3. LLM service is accessible from your network
4. Check logs: `tail -f logs/app.log`

### WebSocket Connection Fails

**Common Issues**:
1. Browser blocks WebSocket (check browser console)
2. Proxy/firewall blocks WebSocket
3. Server not running on correct address

**Solution**: Use curl to test endpoint availability first

### Sessions Not Being Created

**Check**:
1. Is the session endpoint returning 200 status?
2. Check if agent is properly initialized
3. Verify LLM is accessible and responding

## Performance Considerations

1. **Concurrent Requests**: Each request creates a new agent instance (not pooled)
   - For high concurrency, consider implementing agent pooling

2. **Memory Usage**: Agent instances hold conversation history in memory
   - Implement session cleanup (currently no auto-cleanup)
   - Set `AGENT__SESSION_TTL_SECONDS` appropriately

3. **LLM API Rate Limits**: Monitor API usage
   - Add rate limiting middleware for production
   - Implement request queuing for heavy load

## Security Considerations

1. **API Key Management**:
   - Never commit `.env` with real API keys
   - Use environment variables or secrets management

2. **CORS Configuration**:
   - Currently allows all origins (`*`)
   - Restrict in production: `CORS_ORIGINS=["https://yourdomain.com"]`

3. **Authentication**:
   - Current implementation has no authentication
   - Add JWT/API key authentication for production

4. **Input Validation**:
   - All endpoints validate input using Pydantic
   - Max query length: 5000 characters
   - Additional validation can be added per endpoint

## Next Steps

1. **Configure valid LLM API key** in `.env`
2. **Run test suite** to verify full functionality
3. **Start server** and test via Web UI or API client
4. **Deploy** to production environment
5. **Monitor** health and performance in production

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [API Guide](API_GUIDE.md)
- [Project Architecture](CLAUDE.md)
