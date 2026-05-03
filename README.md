# RadCode

Autonomous AI Software Engineer - Devin-like single agent using OpenHands SDK.

## Architecture

```
RadCode
├── src/
│   ├── coordinator.py    # Thin SDK wrapper
│   ├── tools.py        # Additional tools (sub-agent, sandbox)
│   ├── server.py       # FastAPI server
│   ├── cli.py          # CLI entry point
│   └── skills/         # Domain expertise
├── ui/                 # React frontend
├── deploy/             # Docker deployment
└── start.sh           # Deployment script
```

## Features

- **Single Agent** - Uses OpenHands SDK for all agent logic
- **Multi-Provider** - NVIDIA, Anthropic, OpenAI, Groq, Google
- **Modern UI** - React chat interface (Claude-like)
- **Docker Ready** - Production deployment with Docker Compose
- **WebSocket** - Real-time progress updates

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/ubix08/RadCod.git
cd RadCod
```

### 2. Configure Environment

```bash
cp deploy/env.example .env
# Edit .env with your API keys
```

### 3. Start

```bash
# Using Docker (recommended)
./start.sh setup

# Or manually
python -m src.server
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|-----------|
| `NVIDIA_API_KEY` | NVIDIA API key | If using NVIDIA models |
| `ANTHROPIC_API_KEY` | Anthropic API key | If using Claude |
| `OPENAI_API_KEY` | OpenAI API key | If using GPT models |
| `LLM_MODEL` | Model to use | No (defaults provided) |

### Supported Models

```bash
# Free models (NVIDIA)
LLM_MODEL=meta/llama-3.1-70b-instruct

# Groq (free)
LLM_MODEL=groq/llama-3.1-70b-instruct

# Anthropic
LLM_MODEL=anthropic/claude-sonnet-4-5-20250929

# OpenAI
LLM_MODEL=gpt-4o
```

## Usage

### Python API

```python
from src.coordinator import create_agent

agent = create_agent(workspace="./workspace")
result = agent.run("Create a FastAPI REST API with user authentication")
print(result)
```

### CLI

```bash
python -m src.cli run "Build a Python CLI tool"
```

### REST API

```bash
# Start server
python -m src.server

# Execute task
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"request": "Create a hello world app"}'
```

## Deployment

### Docker Compose (Recommended)

```bash
# Production setup
./start.sh setup

# Or step by step
./start.sh build
./start.sh start
```

### Services

| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

### Commands

```bash
./start.sh setup    # Initial setup
./start.sh start   # Start services
./start.sh stop   # Stop services
./start.sh status # Show status
./start.sh logs   # View logs
./start.sh reset  # Full reset
```

## API Endpoints

### Server (`/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info |
| `/health` | GET | Health check |
| `/run` | POST | Execute task |
| `/metrics` | GET | Token metrics |
| `/deploy` | POST | Deploy project |
| `/ws` | WS | WebSocket |

### Admin (`/api/v1`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tasks` | POST | Create task |
| `/tasks` | GET | List tasks |
| `/workspaces` | GET | List workspaces |
| `/config` | GET/PATCH | Config |
| `/metrics` | GET | Usage metrics |
| `/health` | GET | System health |

## Development

```bash
# Install dependencies
pip install -e .

# Run server
python -m src.server

# Run frontend
cd ui && npm install && npm run dev
```

## Tech Stack

- **Backend**: Python, FastAPI, OpenHands SDK
- **Frontend**: React, Vite
- **Deployment**: Docker, Nginx

## License

MIT
