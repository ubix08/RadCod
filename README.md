# Radcod

Autonomous AI Software Engineer Orchestrator.

This system is designed to run 24/7, orchestrated by a main agent coordinator that delegates tasks to specialized agents (e.g., Coding Agent, Deep Search Agent, Browser Agent).

## Architecture

Radcod utilizes the `openhands-sdk` to manage the Coding Agent component, ensuring a modular and maintainable design.

## Project Structure
- `src/orchestrator/`: Main coordinator logic.
- `src/agents/`: Specialized agent definitions (Deep Search, Browser).
- `src/integrations/`: Integrations, including the `coding_agent` wrapper.

## Quick Start

```python
from src.integrations.coding_agent.wrapper import CodingAgentWrapper

# Initialize the coding agent
coder = CodingAgentWrapper(model_name="openai/gpt-4o", workspace_path="./workspace")

# Delegate a task
coder.run_task("Implement a new feature in the codebase")
```
