"""
RadCod Agentic Core - SDK Integrated
====================================
Implements agentic tasks using the native OpenHands SDK.
"""

from typing import Any
from openhands_clone.agent import coding_agent

# =============================================================================
# High-Level API (SDK Integrated)
# =============================================================================

def execute_task(
    task: str,
    model: str = "anthropic/claude-sonnet-4-20250513",
    api_key: str | None = None,
    workspace: str | None = None,
    max_iterations: int = 100,
    verbose: bool = False,
) -> str:
    """
    Execute a task using the native SDK-based Agentic loop.
    """
    convo = coding_agent(
        model=model,
        api_key=api_key,
        workspace=workspace,
        max_iterations=max_iterations,
    )
    
    convo.send_message(task)
    convo.run()
    
    metrics = convo.get_metrics()
    return f"Task completed. Metrics: {metrics}"

def create_agentic_conversation(
    model: str = "anthropic/claude-sonnet-4-20250513",
    workspace: str | None = None,
) -> Any:
    """Create an agentic conversation (for SDK compatibility)."""
    return coding_agent(model=model, workspace=workspace)
