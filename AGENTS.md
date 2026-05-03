# RadCode - Single Agent Architecture (Devin Pattern)

## Core Principle

**ONE autonomous Agent** that handles all tasks using:
- TaskTrackerTool for subtask management
- TerminalTool for command execution  
- FileEditorTool for code writing

## Final Architecture

```
RadcodeCoordinator
└── ONE Agent (LLM + 3 Tools)
    ├── TaskTrackerTool  → Track subtasks
    ├── TerminalTool   → Run commands
    └── FileEditorTool → Write code
```

## Files

```
src/
├── cli.py                         # Simple CLI
└── orchestrator/
    ├── coordinator.py             # SINGLE AGENT (THE WHOLE SYSTEM)
    └── domain_spec/
        ├── models.py             # Domain data models
        └── prompt.py            # (unused, can delete)
```

## SDK Components Used

```python
from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.terminal import TerminalTool
```

## How It Works

1. User: "Build a CRM"
2. Agent receives task
3. Uses TaskTrackerTool to plan subtasks
4. Uses TerminalTool/FileEditorTool to execute
5. Reports completion

## Simplified

- ✅ Single Agent
- ✅ TaskTrackerTool for subtasks
- ✅ TerminalTool + FileEditorTool
- ✅ Matches Devin architecture

## Devin Parity: ~70%

## Setup

```bash
pip install openhands-sdk openhands-tools
export LLM_API_KEY="your-key"
```

## Usage

```bash
python -m src.cli run "Build a CRM"