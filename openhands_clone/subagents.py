"""
OpenHands-Clone Sub-Agents
=========================
Sub-agent delegation and parallel execution.

This module provides support for delegating work to specialized sub-agents.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable


# =============================================================================
# Sub-Agent Base
# =============================================================================

class SubAgent:
    """Base class for sub-agents."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    def execute(self, task: str) -> Any:
        """Execute a task. Override in subclass."""
        raise NotImplementedError
    
    def __repr__(self) -> str:
        return f"<SubAgent: {self.name}>"


# =============================================================================
# Function-Based Sub-Agent
# =============================================================================

class FunctionSubAgent(SubAgent):
    """Sub-agent that wraps a function."""
    
    def __init__(
        self,
        name: str,
        func: Callable[[str], Any],
        description: str = "",
    ):
        super().__init__(name, description)
        self.func = func
    
    def execute(self, task: str) -> Any:
        return self.func(task)


# =============================================================================
# Parallel Execution
# =============================================================================

def delegate_parallel(
    agents: list[SubAgent],
    tasks: list[str],
) -> list[tuple[str, Any]]:
    """
    Execute tasks in parallel with sub-agents.
    
    Args:
        agents: List of sub-agents
        tasks: List of tasks (one per agent)
    
    Returns:
        List of (agent_name, result) tuples
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=len(agents)) as executor:
        futures = {}
        for agent, task in zip(agents, tasks):
            future = executor.submit(agent.execute, task)
            futures[future] = agent.name
        
        for future in as_completed(futures):
            agent_name = futures[future]
            try:
                result = future.result()
            except Exception as e:
                result = f"Error: {e}"
            results.append((agent_name, result))
    
    return results


def delegate_async(
    agents: list[SubAgent],
    tasks: list[str],
) -> list[tuple[str, Any]]:
    """
    Execute tasks asynchronously with sub-agents.
    
    Args:
        agents: List of sub-agents
        tasks: List of tasks
    
    Returns:
        List of (agent_name, result) tuples
    """
    async def run_agent(agent: SubAgent, task: str) -> tuple[str, Any]:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, agent.execute, task)
        return agent.name, result
    
    async def run_all():
        return await asyncio.gather(*[
            run_agent(agent, task)
            for agent, task in zip(agents, tasks)
        ])
    
    return list(asyncio.run(run_all()))


# =============================================================================
# Sequential Execution
# =============================================================================

def delegate_sequential(
    agents: list[SubAgent],
    tasks: list[str],
) -> list[tuple[str, Any]]:
    """
    Execute tasks sequentially with sub-agents.
    
    Args:
        agents: List of sub-agents
        tasks: List of tasks
    
    Returns:
        List of (agent_name, result) tuples
    """
    results = []
    for agent, task in zip(agents, tasks):
        try:
            result = agent.execute(task)
        except Exception as e:
            result = f"Error: {e}"
        results.append((agent.name, result))
    return results


# =============================================================================
# Built-in Sub-Agent Types
# =============================================================================

class CodeReviewSubAgent(SubAgent):
    """Sub-agent for code review."""
    
    def __init__(self, agent: Any):
        super().__init__("code-review", "Reviews code")
        self.agent = agent
    
    def execute(self, task: str) -> Any:
        convo = self.agent.fork()
        convo.send_message(f"Review this code: {task}")
        convo.run()
        return convo.get_result()


class TestGeneratorSubAgent(SubAgent):
    """Sub-agent for generating tests."""
    
    def __init__(self, agent: Any):
        super().__init__("test-generator", "Generates tests")
        self.agent = agent
    
    def execute(self, task: str) -> Any:
        convo = self.agent.fork()
        convo.send_message(f"Write tests for: {task}")
        convo.run()
        return convo.get_result()


class DocsGeneratorSubAgent(SubAgent):
    """Sub-agent for generating documentation."""
    
    def __init__(self, agent: Any):
        super().__init__("docs-generator", "Generates docs")
        self.agent = agent
    
class ScaffoldingSubAgent(SubAgent):
    """Sub-agent for scaffolding new projects from templates."""
    
    def __init__(self, workspace: str):
        super().__init__("scaffolder", "Scaffolds projects from templates")
        self.workspace = workspace
    
    def execute(self, task: str) -> Any:
        # Task format: "Build name template"
        import shutil
        import os
        
        parts = task.split()
        if len(parts) < 3:
            return "Error: Invalid task format for scaffolder."
        
        name = parts[1]
        template = parts[2]
        
        template_dir = os.path.join(self.workspace, "templates", template)
        target_dir = os.path.join(self.workspace, "apps", name)
        
        if not os.path.exists(template_dir):
            return f"Error: Template {template} not found."
            
        shutil.copytree(template_dir, target_dir)
        return f"Scaffolded {name} from {template} at {target_dir}"


class BrowserSubAgent(SubAgent):
    """Sub-agent for browsing the web."""
    
    def __init__(self, agent: Any):
        super().__init__("browser", "Browses the web")
        self.agent = agent
    
    def execute(self, task: str) -> Any:
        # Use browser tool if available, or simulation
        return f"Browsed for: {task}"


class DeepSearcherSubAgent(SubAgent):
    """Sub-agent for deep searching."""
    
    def __init__(self, agent: Any):
        super().__init__("searcher", "Performs deep searches")
        self.agent = agent
    
    def execute(self, task: str) -> Any:
        # Use search tool if available, or simulation
        return f"Deep searched for: {task}"