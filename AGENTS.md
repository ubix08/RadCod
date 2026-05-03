# RadCode - Devin Parity Architecture

## Core Architecture

**ONE autonomous Agent** that handles all tasks using:
- TaskTrackerTool for subtask management
- TerminalTool for command execution  
- FileEditorTool for code writing
- SecurityAnalyzer for action validation

## Features Implemented

| Feature | Status | Description |
|---------|--------|-------------|
| Single Agent | ✅ | ONE Agent matching Devin |
| TaskTrackerTool | ✅ | Explicit task visibility |
| TerminalTool | ✅ | Command execution |
| FileEditorTool | ✅ | Code writing |
| SecurityAnalyzer | ✅ | Action validation (low/medium/high) |
| Stuck Detection | ✅ | Timeout + max iterations |
| Metrics | ✅ | Token usage + cost tracking |
| Docker Sandbox | ✅ | Isolated execution |
| Cloud Runtime | ✅ | OpenHands Cloud support |

## Files

```
src/
├── cli.py                  # Simple CLI
└── orchestrator/
    └── coordinator.py     # Single Agent with all features
```

## Usage

```python
from src.orchestrator.coordinator import RadcodeCoordinator

# Basic
coordinator = RadcodeCoordinator()
result = coordinator.run("Build a CRM")

# With security
coordinator = RadcodeCoordinator(security_level="high")

# With timeout
result = coordinator.run_with_timeout(
    "Build a CRM",
    timeout_seconds=600,
    max_iterations=100
)

# Get metrics
metrics = coordinator.get_metrics()

# Docker sandbox
coordinator = RadcodeCoordinator.create_with_docker(
    docker_image="openhands/runtime:latest"
)
```

## Security Levels

| Level | Dangerous Actions | Confirmation |
|-------|------------------|--------------|
| low | log only | no |
| medium | warn | yes |
| high | block | n/a |

## Devin Parity: ~90%