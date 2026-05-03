# RadCode

Autonomous AI Software Engineer - Devin-like single agent architecture.

## Architecture

**ONE autonomous Agent** that handles all tasks using OpenHands SDK.

```
src/
├── cli.py           # CLI entry point
└── coordinator.py  # Single Agent (the whole system!)
```

## Features

- Single Agent (Devin pattern)
- TaskTrackerTool for subtask management
- TerminalTool + FileEditorTool for execution
- SecurityAnalyzer for action validation
- Stuck detection with timeout
- Metrics tracking (token/cost)
- Docker sandbox support

## Quick Start

```python
from src.coordinator import RadcodeCoordinator

# Initialize and run
coordinator = RadcodeCoordinator()
result = coordinator.run("Build a CRM system")
```

## CLI

```bash
python -m src.cli run "Build a CRM"
```

## Requirements

- Python 3.10+
- openhands-sdk
- openhands-tools

## Devin Parity: ~90%
