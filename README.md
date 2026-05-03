# RadCode

Autonomous AI Software Engineer - Devin-like single agent architecture.

## Architecture

**ONE autonomous Agent** that handles all tasks using OpenHands SDK.

```
src/
├── coordinator.py   # Single Agent (the whole system!)
├── cli.py           # CLI entry point
├── subagents/          # File-based sub-agents (optional)
│   ├── backend.md  
│   ├── frontend.md
│   └── test.md
└── skills/          # Domain expertise skills
```

## Features

- Single Agent (Devin pattern)
- TaskTrackerTool for subtask management
- TerminalTool + FileEditorTool for execution
- File-based specialized agents
- Skills for domain expertise
- Docker sandbox support

## Quick Start

```python
from src.coordinator import RadcodeCoordinator

# Initialize and run
coordinator = RadcodeCoordinator()
result = coordinator.run("Build a CRM system")

# With timeout
result = coordinator.run_with_timeout("Build a CRM", timeout_seconds=300)
```

## CLI

```bash
python -m src.cli run "Build a CRM"
```

## NVIDIA Integration

RadCode supports NVIDIA NIM via litellm patch:

```python
# Apply patch BEFORE creating coordinator
from src.litellm_patch import patch_litellm
patch_litellm()

# Set model (minimax, llama, z-ai, glm available)
os.environ['LLM_MODEL'] = 'minimaxai/minimax-m2.7'

from src.coordinator import RadcodeCoordinator
coordinator = RadcodeCoordinator()
result = coordinator.run("Build a calculator")
```

### Supported Models

| Model | Status | Notes |
|-------|--------|-------|
| `minimaxai/minimax-m2.7` | ✅ | Thinking model |
| `z-ai/glm4.7` | ✅ | Thinking model |
| `llama-3.1-70b-instruct` | ✅ | Via meta/ prefix |

### Environment Variables

- `NVIDIA_API_KEY` - NVIDIA API key (nvapi-...)
- `NVIDIA_API_BASE` - API base URL (default: https://integrate.api.nvidia.com/v1)
- `LLM_MODEL` - Model name

## Requirements

- Python 3.10+
- openhands-sdk
- openhands-tools

## Devin Parity: 92%
