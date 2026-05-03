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
| SecurityAnalyzer | ✅ |
| Stuck Detection | ✅ |
| Metrics | ✅ |
| Docker Sandbox | ✅ |

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
```

## CLI

```bash
python -m src.cli run "Build a CRM"
```

## Devin Parity: ~90%