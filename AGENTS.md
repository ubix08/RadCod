# Repository Knowledge - RadCod

## Project Overview
RadCod is an agentic coding system built with the OpenHands SDK, designed to mirror the architecture and behavior of OpenHands for local, autonomous coding tasks.

## Key Principles
1. **Multi-Agent Architecture**: Uses specific agents (Planning, Execute, Verify, Browser, etc.) for tasks.
2. **Reasoning-Action Loop**: Continuous feedback loop (Reasoning -> Action -> Observation) until task completion.
3. **State Persistence**: Memory maintained across agent calls.
4. **Tool-Driven**: Uses `file_editor`, `Terminal`, `Browser` as primary tools.
5. **Verification-First**: Validates actions before claiming success.

## Project Structure
- `openhands_clone/`: Core logic
    - `agentic.py`: Core reasoning-action loop
    - `multi_agent.py`: Multi-agent pipeline
    - `orchestrator.py`: Task orchestration
    - `skills.py`: Skill registry (code-review, debug, refactor, etc.)
    - `tool_executor.py`: Tool execution logic

## Workflow
1. User input triggers a message event.
2. Agent performs reasoning (parsing intent, checking skills, creating plan).
3. Agent executes actions (tools).
4. Security checks validate actions.
5. Observation (result) is returned to the agent.
6. Loop continues until verification and completion.

## Development Guidelines
- Always follow the reasoning-action loop.
- Use existing tools (`file_editor`, `Terminal`).
- Add new agents/skills by extending base classes.
- Refer to `SPEC.md` and `WORKFLOW.md` for detailed specifications and flows.
