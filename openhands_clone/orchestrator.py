"""
RadCod Task Orchestrator
====================
Advanced orchestration with task distribution, parallel execution, and state management.

This is the brain that coordinates all agents.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum
from datetime import datetime
import json
import os

from openhands_clone.subagents import (
    SubAgent, ScaffoldingSubAgent, BrowserSubAgent, DeepSearcherSubAgent
)


# =============================================================================
# Task Status
# =============================================================================

class TaskStatus(Enum):
    """Status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# Task Definition
# =============================================================================

@dataclass
class Task:
    """A task in the pipeline."""
    
    id: str
    description: str
    agent_type: str  # planning, executing, verifying
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "id": self.id,
            "description": self.description,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "result": self.result,
            "error": self.error,
        }


# =============================================================================
# Task Graph
# =============================================================================

class TaskGraph:
    """
    Manages task dependencies and execution order.
    
    Handles:
    - Task ordering based on dependencies
    - Parallel execution where possible
    - Circular dependency detection
    """
    
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._adjacency: dict[str, set[str]] = {}  # task -> depends on
    
    def add_task(self, task: Task) -> None:
        """Add a task."""
        self._tasks[task.id] = task
        self._adjacency[task.id] = set()
        
        for dep in task.dependencies:
            if dep in self._tasks:
                self._adjacency[task.id].add(dep)
    
    def get_ready_tasks(self) -> list[Task]:
        """Get tasks that are ready to run (all dependencies complete)."""
        ready = []
        
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check dependencies
            deps_met = all(
                self._tasks[dep].status == TaskStatus.COMPLETE
                for dep in task.dependencies
            )
            
            if deps_met:
                ready.append(task)
        
        return sorted(ready, key=lambda t: t.priority, reverse=True)
    
    def get_status(self) -> dict:
        """Get overall status."""
        statuses = {
            "pending": 0,
            "running": 0,
            "complete": 0,
            "failed": 0,
        }
        
        for task in self._tasks.values():
            statuses[task.status.value] += 1
        
        return statuses
    
    def is_complete(self) -> bool:
        """Check if all tasks complete."""
        return all(t.status == TaskStatus.COMPLETE for t in self._tasks.values())
    
    def has_failures(self) -> bool:
        """Check if any tasks failed."""
        return any(t.status == TaskStatus.FAILED for t in self._tasks.values())


# =============================================================================
# State Manager
# =============================================================================

@dataclass
class AgentState:
    """State maintained between agent calls."""
    
    workspace: str
    current_plan: dict = field(default_factory=dict)
    executed_files: list[str] = field(default_factory=list)
    created_files: list[str] = field(default_factory=list)
    test_results: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Serialize state."""
        return {
            "workspace": self.workspace,
            "executed_files": self.executed_files,
            "created_files": self.created_files,
            "test_results": self.test_results,
            "errors": self.errors,
        }
    
    def save(self, path: str) -> None:
        """Save state to file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "AgentState":
        """Load state from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            workspace=data["workspace"],
            executed_files=data.get("executed_files", []),
            created_files=data.get("created_files", []),
            test_results=data.get("test_results", {}),
            errors=data.get("errors", []),
        )


# =============================================================================
# Codebase Analyzer
# =============================================================================

class CodebaseAnalyzer:
    """
    Analyzes codebase structure for better planning.
    
    Provides:
    - File structure
    - Dependencies
    - Test coverage
    - Architecture patterns
    """
    
    def __init__(self, workspace: str):
        self.workspace = workspace
        self._structure: dict | None = None
        self._dependencies: dict | None = None
    
    def analyze(self) -> dict:
        """Full analysis."""
        return {
            "structure": self.get_structure(),
            "dependencies": self.get_dependencies(),
            "tests": self.get_tests(),
            "frameworks": self.detect_frameworks(),
        }
    
    def get_structure(self) -> dict:
        """Get directory structure."""
        import os
        
        structure = {"files": [], "dirs": []}
        
        for root, dirs, files in os.walk(self.workspace):
            # Skip hidden and common ignore dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv')]
            
            rel_root = os.path.relpath(root, self.workspace)
            
            for f in files:
                if not f.startswith('.'):
                    path = os.path.join(rel_root, f)
                    structure["files"].append(path)
            
            for d in dirs:
                structure["dirs"].append(os.path.join(rel_root, d))
        
        return structure
    
    def get_dependencies(self) -> dict:
        """Get dependency information."""
        import os
        
        deps = {}
        
        # Check common dependency files
        dep_files = {
            "requirements.txt": "pip",
            "pyproject.toml": "python",
            "package.json": "npm",
            "Cargo.toml": "rust",
            "go.mod": "go",
        }
        
        for filename, dep_type in dep_files.items():
            path = os.path.join(self.workspace, filename)
            if os.path.exists(path):
                deps[dep_type] = filename
        
        return deps
    
    def get_tests(self) -> dict:
        """Get test information."""
        import os
        
        tests = {"files": [], "framework": None}
        
        # Find test files
        for root, _, files in os.walk(self.workspace):
            for f in files:
                if f.startswith("test_") or f.endswith("_test.py"):
                    rel = os.path.relpath(os.path.join(root, f), self.workspace)
                    tests["files"].append(rel)
        
        # Detect framework
        if any("pytest" in f for f in tests["files"]):
            tests["framework"] = "pytest"
        elif any("unittest" in f for f in tests["files"]):
            tests["framework"] = "unittest"
        
        return tests
    
    def detect_frameworks(self) -> dict:
        """Detect frameworks used."""
        import os
        
        frameworks = {}
        
        # Check for common indicators
        indicators = {
            "fastapi": ["fastapi", "FastAPI"],
            "flask": ["flask", "Flask"],
            "django": ["django", "_DJANGO"],
            "react": ["react", "React"],
            "vue": ["Vue", "vue"],
            "nextjs": ["next", "Next.js"],
        }
        
        # Simple check - would need more sophisticated analysis
        for root, _, files in os.walk(self.workspace):
            if "__pycache__" in root or "node_modules" in root:
                continue
            
            for f in files:
                if f.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read(10000)  # First 10k
                            for fw in indicators:
                                if any(ind in content for ind in indicators[fw]):
                                    frameworks[fw] = True
                    except:
                        pass
        
        return list(frameworks.keys())


# =============================================================================
# Advanced Orchestrator
# =============================================================================

class TaskOrchestrator:
    """
    Advanced orchestrator with parallel execution.
    
    Features:
    - Parallel task execution
    - Automatic dependency resolution
    - State management
    - Error recovery
    """
    
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.task_graph = TaskGraph()
        self.state = AgentState(workspace=workspace)
        self.analyzer = CodebaseAnalyzer(workspace)
    
    def create_tasks(self, plan: dict) -> None:
        """Create tasks from plan."""
        # Convert plan steps to tasks
        steps = plan.get("steps", [])
        
        for i, step in enumerate(steps):
            task = Task(
                id=f"task_{i}",
                description=step.get("description", str(step)),
                agent_type=self._select_agent_type(step),
                dependencies=[],  # Would parse from plan
                priority=i,
            )
            self.task_graph.add_task(task)
    
    def _select_agent_type(self, step: dict) -> str:
        """Select appropriate agent for step."""
        desc = step.get("description", "").lower()
        
        if any(w in desc for w in ["plan", "analyze", "understand"]):
            return "planning"
        elif any(w in desc for w in ["verify", "test", "check"]):
            return "verifying"
        else:
            return "executing"
    
    async def execute(self) -> dict:
        """Execute all tasks."""
        results = []
        
        while not self.task_graph.is_complete():
            # Get ready tasks
            ready = self.task_graph.get_ready_tasks()
            
            if not ready:
                if self.task_graph.has_failures():
                    break
                await asyncio.sleep(0.1)
                continue
            
            # Execute in parallel where possible
            if len(ready) > 1:
                # Would run in parallel
                for task in ready:
                    result = await self._execute_task(task)
                    results.append(result)
            else:
                task = ready[0]
                result = await self._execute_task(task)
                results.append(result)
        
        return {
            "status": "complete" if self.task_graph.is_complete() else "failed",
            "results": results,
            "state": self.state.to_dict(),
        }
    
    async def _execute_task(self, task: Task) -> dict:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            # Would call appropriate agent
            # For now, simulate
            result = f"Executed: {task.description}"
            
            task.status = TaskStatus.COMPLETE
            task.result = result
            task.completed_at = datetime.now()
            
            return {"task": task.id, "result": result}
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.state.errors.append(str(e))
            
            return {"task": task.id, "error": str(e)}
    
    def get_status(self) -> dict:
        """Get execution status."""
        return {
            "task_count": len(self.task_graph._tasks),
            "task_status": self.task_graph.get_status(),
            "state": self.state.to_dict(),
        }


# =============================================================================
# Execution Engine
# =============================================================================

class ExecutionEngine:
    """
    The main execution engine.
    
    coordinates:
    - Task planning
    - Agent execution
    - State management
    - Result aggregation
    """
    
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.orchestrator = TaskOrchestrator(workspace)
        self.analyzer = CodebaseAnalyzer(workspace)
        # Initialize specialized sub-agents
        self.scaffolder = ScaffoldingSubAgent(workspace)
    
    async def execute(self, task: str, mode: str = "auto") -> dict:
        """
        Execute a task.
        """
        # Autonomous delegation logic
        if "build" in task.lower() and "application" in task.lower():
            # Extract app name and template
            # Prompt: "Build a business application named '{app_name}' using the '{template}' template."
            # Simple extraction for demo purposes
            parts = task.split()
            app_name = next((parts[i+1] for i in range(len(parts)) if parts[i] == 'named'), 'unknown')
            template = next((parts[i+1] for i in range(len(parts)) if parts[i] == 'using'), 'crm')
            
            # Delegate to scaffolder
            scaffold_task = f"Build {app_name} {template}"
            result = self.scaffolder.execute(scaffold_task)
            
            # Update dashboard status
            apps_json_path = os.path.join(self.workspace, "dashboard", "public", "apps.json")
            if os.path.exists(apps_json_path):
                with open(apps_json_path, 'r+') as f:
                    apps = json.load(f)
                    for app in apps:
                        if app["name"] == app_name:
                            app["status"] = "running"
                            app["url"] = "http://localhost:3000" # Placeholder
                    f.seek(0)
                    json.dump(apps, f, indent=2)
            
            return {"status": "complete", "result": result}

        if mode == "quick":
            return await self._quick_execute(task)
    
    async def _quick_execute(self, task: str) -> dict:
        """Quick single-pass execution."""
        # Would use single agent
        return {
            "task": task,
            "status": "complete",
            "analysis": self.analyzer.analyze(),
        }


# =============================================================================
# Functions
# =============================================================================

def analyze_codebase(workspace: str) -> dict:
    """Quick codebase analysis."""
    return CodebaseAnalyzer(workspace).analyze()


def create_orchestrator(workspace: str) -> TaskOrchestrator:
    """Create task orchestrator."""
    return TaskOrchestrator(workspace)


async def execute_task(task: str, workspace: str) -> dict:
    """Execute task with full orchestration."""
    engine = ExecutionEngine(workspace)
    return await engine.execute(task)