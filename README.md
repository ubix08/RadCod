# OpenHands-Clone

An optimized agentic coding system built with the OpenHands SDK.

## Features

- **Core SDK**: LLM configuration, Agent with reasoning-action loop, Conversation management
- **Custom Tools**: file_editor, terminal, task_tracker (compatible implementations)
- **Skills**: code-review, debug, refactor, test, docs, security
- **Sub-Agents**: Parallel and sequential delegation
- **Streaming**: Real-time response streaming
- **Persistence**: Save and restore conversation state
- **Metrics**: Token usage and cost tracking

## Quick Start

```python
from openhands_clone import coding_agent

convo = coding_agent()
convo.send_message("Create a simple hello world app")
convo.run()
```

## Installation

```bash
pip install openhands-clone
# or
pip install -e .
```

## CLI Usage

```bash
# Basic task
ohand "Create a hello world app"

# With specific model
ohand "Fix this bug" --model anthropic/claude-opus-4-20250513

# Stream responses
ohand --stream "List files"

# Interactive mode
ohand --interactive
```

## Configuration

```python
from openhands_clone import coding_agent

convo = coding_agent(
    model="anthropic/claude-sonnet-4-20250513",
    api_key="your-api-key",  # or set LLM_API_KEY env var
    base_url=None,  # for custom LLM endpoints
    workspace="/path/to/project",
    max_iterations=100,
)
```

## Skills

```python
from openhands_clone import get_skill

# Activate a skill
skill = get_skill("code-review")
print(skill.get_prompt())

# Available skills
from openhands_clone import list_skills
print(list_skills())
# ['code-review', 'debug', 'refactor', 'test', 'docs', 'security']
```

## Sub-Agents

```python
from openhands_clone.subagents import (
    SubAgent,
    FunctionSubAgent,
    delegate_parallel,
)

# Create sub-agents
def processor(task):
    return f"Processed: {task}"

def analyzer(task):
    return f"Analyzed: {task}"

agents = [
    FunctionSubAgent("proc", processor),
    FunctionSubAgent("anl", analyzer),
]

# Execute in parallel
results = delegate_parallel(agents, ["data1", "data2"])
```

## Examples

See `examples.py` for more usage examples.

## Environment Variables

- `LLM_API_KEY` - API key for LLM provider
- `LLM_MODEL` - Default model (default: anthropic/claude-sonnet-4-20250513)
- `LLM_BASE_URL` - Custom base URL for LLM API

## License

MIT