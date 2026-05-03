# RadCode - Devin Parity Architecture

## Core Architecture

**ONE autonomous Agent** that handles all tasks:

```
src/
├── cli.py           # CLI entry point
└── coordinator.py  # Single Agent (the whole system!)
```

## Features

| Feature | Status |
|---------|--------|
| Single Agent | ✅ |
| TaskTrackerTool | ✅ |
| TerminalTool | ✅ |
| FileEditorTool | ✅ |
| BrowserToolSet | ✅ (core) |
| SecurityAnalyzer | ✅ |
| Stuck Detection | ✅ |
| Metrics | ✅ |
| Docker Sandbox | ✅ |
| Context Condensation | ✅ |
| Progress Callbacks | ✅ |
| Deployment Helpers | ✅ |
| SWE-bench Eval | ⚠️ (framework) |

## Usage

```python
from src.coordinator import RadcodeCoordinator

# Basic
coordinator = RadcodeCoordinator()
result = coordinator.run("Build a CRM")

# With security level
coordinator = RadcodeCoordinator(security_level="high")

# With timeout
result = coordinator.run_with_timeout("Build a CRM", timeout_seconds=600)

# Docker sandbox
coordinator = RadcodeCoordinator.create_with_docker()

# Context management
if not coordinator.can_continue():
    coordinator.condense_context()

# Progress callback
def on_progress(e):
    print(f"Progress: {e}")
result = coordinator.run("Build a CRM", progress_callback=on_progress)

# Deployment
coordinator.deploy_to_vercel("/path/to/project", "my-app")
```

## CLI

```bash
python -m src.cli run "Build a CRM"
python -m src.cli config
```

## Deployment

```bash
# Vercel
python -m src.deploy vercel /path/to/project --name my-app --token $VERCEL_TOKEN

# Docker
python -m src.deploy docker /path/to/project myapp --push
```

## Benchmarking

```bash
# Run SWE-bench evaluation
python benchmarks/swebench.py django#12345
```

## Testing

```bash
pytest tests/
```

## Server

```bash
# Start server
python -m src.cli server --port 8000

# Or directly
python -m src.server

# API available at http://localhost:8000
# - POST /run - Execute task
# - GET /metrics - Get metrics
# - GET /context - Context summary
# - POST /deploy - Deploy project
# - WS /ws - WebSocket progress
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info |
| `/health` | GET | Health check |
| `/run` | POST | Execute task |
| `/run/{task_id}` | GET | Task status |
| `/metrics` | GET | Token/cost metrics |
| `/context` | GET | Context summary |
| `/deploy` | POST | Deploy project |
| `/ws` | WS | Progress stream |

## Admin API (api/v1)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | System health + memory |
| `/api/v1/diagnostics` | GET | Config validation |
| `/api/v1/tasks` | POST | Create task |
| `/api/v1/tasks` | GET | List tasks |
| `/api/v1/tasks/{id}` | GET | Task status |
| `/api/v1/tasks/{id}` | DELETE | Cancel task |
| `/api/v1/workspaces` | POST | Create workspace |
| `/api/v1/workspaces` | GET | List workspaces |
| `/api/v1/workspaces/{name}` | GET | Workspace details |
| `/api/v1/workspaces/{name}` | DELETE | Delete workspace |
| `/api/v1/config` | GET | Get config |
| `/api/v1/config` | PATCH | Update config |
| `/api/v1/metrics` | GET | Usage metrics |
| `/api/v1/agent/status` | GET | Agent status |
| `/api/v1/context` | GET | Context summary |
| `/api/v1/context/condense` | POST | Condense context |

# RadCode UI

```bash
cd ui
npm install
npm run dev
```

Then open http://localhost:5173

## Features

- Modern dark theme with cyan accents
- Mobile-first responsive design
- Real-time progress via WebSocket
- Task polling for status updates
- Workspace selector
- Status indicators

## File Structure

```
ui/
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── index.css
│   ├── components/
│   │   ├── Sidebar.jsx
│   │   ├── ChatArea.jsx
│   │   └── Header.jsx
│   └── hooks/
│       └── useWebSocket.js
├── package.json
└── vite.config.js
```

## Devin Parity: ~90%