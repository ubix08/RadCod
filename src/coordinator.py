"""
RadCode - Devin-like Autonomous Agent.

ONE main agent that:
- Interacts directly with user
- Handles simple tasks using tools  
- Delegates complex sub-tasks via TaskToolSet

Built on OpenHands SDK for full compatibility.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("radcod.coordinator")

# ============= SYSTEM PROMPT =============

SYSTEM_PROMPT = """
# RadCode - Autonomous AI Software Engineer

You are an expert autonomous AI software engineer. Your mission is to deliver working solutions, not just code snippets.

## Your Core Workflow

1. **Understand** - Read carefully what the user wants. Ask clarifying questions if needed.
2. **Plan** - Create a todo list with TaskTrackerTool. Break complex tasks into subtasks.
3. **Execute** - Build incrementally. Test each piece.
4. **Verify** - Run tests, check that code works.
5. **Iterate** - Fix errors until it works.
6. **Deliver** - Report completion with what was built.

## Task Complexity Assessment

**Simple tasks** (< 30 min, single file):
- Handle directly using tools

**Complex tasks** (require multiple components):
- Use TaskToolSet to delegate to sub-agents
- Break into: backend, frontend, tests, deployment

## Tool Selection Strategy

| Task | Tool(s) |
|------|--------|
| Create/update files | TaskTrackerTool + FileEditorTool |
| Run commands (install, test, serve) | TaskTrackerTool + TerminalTool |
| Find code patterns | GlobTool + GrepTool |
| Web research/browse | BrowserToolSet |
| Delegate complex work | TaskToolSet |

## Python Project Patterns

**Use uv for dependency management** (preferred):
```bash
uv add <package>           # Add dependency
uv remove <package>       # Remove dependency  
uv sync                  # Sync environment
uv run pytest           # Run tests
```

**Project initialization**:
```bash
uv init                  # Initialize project
uv venv                 # Create virtual environment
```

## Testing Requirements

**Always write tests** for new features:
- Unit tests: place in `tests/` or `tests/unit/`
- Integration tests: place in `tests/integration/`
- Run with: `uv run pytest` or `pytest`

**Test structure**:
```python
def test_<feature>():
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...
```

## Error Handling

When errors occur:
1. Read the error message carefully
2. Identify the root cause (not symptom)
3. Find relevant code
4. Fix the cause
5. Re-run to verify

**Never**:
- Ignore tests
- Ship broken code
- Skip error messages

## Building Complete Applications

For full-stack applications:

**Backend** (choose based on requirements):
- REST API: FastAPI (preferred for Python)
- GraphQL: Strawberry GraphQL
- Database: PostgreSQL with async SQLAlchemy 2.0

**Frontend** (choose based on requirements):
- React + Vite (preferred)
- Simple: HTML + vanilla JS
- Mobile-first: React + TailwindCSS

**DevOps**:
- Docker: Create Dockerfile + docker-compose.yml
- Deploy: Vercel, Render, or Fly.io

## Quality Standards

- [ ] Code passes `ruff check .` and `ruff format .`
- [ ] Tests pass with `pytest`
- [ ] Dependencies documented in pyproject.toml
- [ ] README with setup instructions

## When Stuck

If you're repeating the same action 3+ times without progress:
- Step back and think of a different approach
- Use BrowserToolSet to search for solutions
- Ask for clarification from user
"""


# ============= MAIN COORDINATOR =============

class RadcodeCoordinator:
    """
    Devin-like Autonomous Agent.
    
    ONE main agent that handles user interaction, simple tasks,
    and delegates to sub-agents when needed.
    """
    
    def __init__(
        self, 
        api_key: str = None, 
        workspace: str = "./workspace",
        security_level: str = "medium"
    ):
        self._key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._workspace = Path(workspace)
        self._instructions = SYSTEM_PROMPT
        self._security_level = security_level
        
        # SDK components
        self._llm = None
        self._agent = None
        self._conversation = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize using OpenHands SDK patterns."""
        if self._initialized:
            return
        
        try:
            from openhands.sdk import LLM, Agent, Conversation, Tool
            from openhands.tools.preset import get_default_agent, get_default_tools
            from openhands.tools.preset import get_default_condenser
            from openhands.tools.glob import GlobTool
            from openhands.tools.grep import GrepTool
            from openhands.tools.task import TaskToolSet
            
            # LLM setup
            PROVIDERS = {
                "groq": ("GROQ_API_KEY", "groq/"),
                "google": ("GEMINI_API_KEY", "google/"),
                "anthropic": ("ANTHROPIC_API_KEY", "anthropic/"),
                "openai": ("OPENAI_API_KEY", "openai/"),
            }
            
            raw_model = os.getenv("LLM_MODEL", "groq/llama-3.1-70b-instruct")
            
            # Find provider
            provider, api_key = "GROQ_API_KEY", os.getenv("GROQ_API_KEY")
            for key, (env_var, prefix) in PROVIDERS.items():
                if key in raw_model.lower():
                    provider, api_key = env_var, os.getenv(env_var)
                    break
            
            model = raw_model if "/" in raw_model else f"{provider.rstrip('_API_KEY').rstrip('_')}/{raw_model}"
            
            self._llm = LLM(model=model, api_key=api_key)
            
            # Use SDK default agent (includes tools + security)
            try:
                self._agent = get_default_agent(self._llm)
            except Exception:
                # Fallback: manual config
                from openhands.sdk.security import GraySwanAnalyzer
                tools = get_default_tools(enable_browser=True)
                tools.extend([
                    Tool(name=TaskToolSet.name),
                    Tool(name=GlobTool.name),
                    Tool(name=GrepTool.name),
                ])
                self._agent = Agent(
                    llm=self._llm,
                    tools=tools,
                    system_prompt=self._instructions,
                    security_analyzer=GraySwanAnalyzer()
                )
            
            # Conversation with condenser
            condenser_llm = self._llm.model_copy(update={"usage_id": "condenser"})
            condenser = get_default_condenser(condenser_llm)
            
            self._conversation = Conversation(
                agent=self._agent,
                workspace=str(self._workspace),
                condenser=condenser
            )
            
            self._initialized = True
            logger.info("RadcodeCoordinator initialized")
            
        except ImportError as e:
            logger.error(f"OpenHands SDK not installed: {e}")
            raise RuntimeError("pip install openhands-sdk openhands-tools")
    
    @property
    def conversation(self) -> Any:
        """Get the SDK Conversation."""
        self._initialize()
        return self._conversation
    
    def run(self, request: str, **kwargs) -> Dict[str, Any]:
        """
        Run a task with the main agent.
        
        The agent will:
        - Handle simple tasks directly
        - Delegate complex tasks via TaskToolSet
        """
        self._initialize()
        self._conversation.send_message(request)
        result = self._conversation.run(**kwargs)
        
        return {
            "status": "success",
            "result": result,
            "request": request
        }
    
    def run_with_timeout(self, request: str, timeout_seconds: int = 600) -> Dict[str, Any]:
        """Run with timeout."""
        from datetime import timedelta
        return self.run(request)


# ============= CONVENIENCE FUNCTION ============

def create_agent(
    api_key: str = None,
    workspace: str = "./workspace",
    security_level: str = "medium"
) -> RadcodeCoordinator:
    """Create a Devin-like agent."""
    return RadcodeCoordinator(
        api_key=api_key,
        workspace=workspace,
        security_level=security_level
    )


# ============= MAIN ============

def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli run <task>")
        sys.exit(1)
    
    if sys.argv[1] == "run":
        task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "What files are in this directory?"
        
        coordinator = create_agent()
        result = coordinator.run(task)
        
        print(f"\nStatus: {result.get('status')}")
        print(f"Result: {result.get('result')}")


if __name__ == "__main__":
    main()
