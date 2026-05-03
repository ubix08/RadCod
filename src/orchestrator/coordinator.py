"""
Radcod Coordinator - Agent Task Management.

Manages:
- INTERNAL TASKS: Coordinator's todo list (what to execute)
- PROJECT: ProjectTODO.md (context + progress)

Flow:
1. receive(request)
2. observe_analyze_evaluate(request)
3. plan(analysis)
4. execute(task)
5. update ProjectTODO.md
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


logger = logging.getLogger("radcod.coordinator")

# ============= INSTRUCTIONS =============

SYSTEM_PROMPT = """
# Coordinator Agent

You are an autonomous AI software engineer coordinating other agents.

## Your Job

1. RECEIVE user request
2. OBSERVE - read carefully
3. ANALYZE - what entities, integrations?
4. EVALUATE - complexity level?
5. PLAN - create internal task list
6. EXECUTE - run tasks via agents

## Internal Task Management

Maintain YOUR internal task list:

```
My Tasks:
- [ ] Call business_analyst → get entities
- [ ] Call database → generate schema
- [ ] Call coding → build app
```

Update status as you execute.

## ProjectTODO.md

Each project has ProjectTODO.md:
- Project name, description
- User context  
- Progress tracking

Update as project advances.

## Task Types

| Task | Agent | Description |
|------|-------|-------------|
| analyze | business_analyst | Identify entities |
| schema | database | Generate database |
| build | coding | Implement app |
| test | browser | Test app |
| research | deep_search | Research |
| plan | architect | Master plan |
| validate | validator | Validate |

## Complexity Guidelines

Based on your judgment:
- SIMPLE: 1-2 entities
- MODERATE: 3-5 entities
- COMPLEX: 6+ entities, integrations
- ENTERPRISE: Full system
"""


# ============= TASK CLASS =============

@dataclass
class Task:
    """Internal task in coordinator's task list."""
    id: str
    action: str      # What to do
    agent: str      # Delegate to whom
    depends_on: List[str] = field(default_factory=list)
    status: str = "pending"  # pending/running/done/failed
    
    def to_markdown(self) -> str:
        checked = "x" if self.status == "done" else " "
        dep = f" (after: {self.depends_on})" if self.depends_on else ""
        return f"- [{checked}] {self.action} → {self.agent}{dep}"


# ============= COORDINATOR =============

class SmartCoordinator:
    """
    Coordinator with internal task management.
    
    Two concepts:
    - PROJECT: Business app being built (ProjectTODO.md)
    - TASKS: Coordinator's internal list
    """
    
    def __init__(self, api_key: str = None, workspace: str = "./workspace"):
        self._key = api_key or os.getenv("OPENAI_API_KEY")
        self._workspace = Path(workspace)
        self._instructions = SYSTEM_PROMPT
        self._tasks: List[Task] = []
        self._next_id = 0
        self._project: Dict[str, Any] = {}
    
    # ----- STEP 1: RECEIVE -----
    
    def receive(self, request: str) -> Dict[str, Any]:
        """Step 1: Receive request."""
        return {
            "status": "received",
            "request": request,
            "next": "Observe, analyze, evaluate"
        }
    
    # ----- STEP 2-3: OBSERVE, ANALYZE, EVALUATE -----
    
    def observe_analyze_evaluate(self, request: str) -> Dict[str, Any]:
        """
        Steps 2-3: Observe, analyze, evaluate.
        
        Coordinator analyzes request internally.
        """
        text = request.lower()
        
        # Entity estimation
        entities = 1
        for word in ["user", "customer", "order", "product", "inventory", 
                   "invoice", "payment", "supplier", "employee", "category"]:
            if word in text:
                entities += 1
        
        # Complexity evaluation
        if "enterprise" in text or "large scale" in text:
            complexity = "enterprise"
        elif "multi" in text or "complex" in text:
            complexity = "complex"
        elif entities > 3 or "system" in text:
            complexity = "moderate"
        else:
            complexity = "simple"
        
        # Integrations check
        integrations = []
        if "accounting" in text: integrations.append("accounting")
        if "payment" in text: integrations.append("payment")
        if "crm" in text: integrations.append("crm")
        
        return {
            "entities": entities,
            "complexity": complexity,
            "integrations": integrations,
            "request": request
        }
    
    # ----- STEP 4: PLAN -----
    
    def plan(self, request: str, analysis: Dict) -> List[Task]:
        """
        Step 4: Outline internal task list.
        
        Creates coordinator's internal todo list.
        """
        self._tasks = []
        self._next_id = 0
        cx = analysis["complexity"]
        
        # Store project info
        self._project = {
            "name": request.split()[2:4] if len(request.split()) > 2 else "Project",
            "complexity": cx,
            "started": datetime.now().isoformat()
        }
        
        # Build task list based on complexity
        if cx == "simple":
            self._add("Call business_analyst", "business_analyst")
            self._add("Call database", "database", after=[0])
            self._add("Call coding", "coding", after=[1])
        
        elif cx == "moderate":
            self._add("Call business_analyst", "business_analyst")
            self._add("Call database", "database", after=[0])
            self._add("Call coding", "coding", after=[1])
            self._add("Call validator", "validator", after=[0])
        
        elif cx == "complex":
            self._add("Call deep_search", "deep_search")
            self._add("Call business_analyst", "business_analyst", after=[0])
            self._add("Call architect", "architect", after=[1])
            self._add("Call database", "database", after=[2])
            self._add("Call coding", "coding", after=[3])
        
        else:  # enterprise
            self._add("Call deep_search", "deep_search")
            self._add("Call business_analyst", "business_analyst", after=[0])
            self._add("Call architect", "architect", after=[1])
            self._add("Call database", "database", after=[2])
            self._add("Call coding", "coding", after=[3])
            self._add("Call browser", "browser", after=[4])
        
        return self._tasks
    
    def _add(self, action: str, agent: str, after: List[int] = None):
        """Add internal task."""
        deps = [f"task_{i}" for i in (after or [])]
        task = Task(f"task_{self._next_id}", action, agent, deps)
        self._tasks.append(task)
        self._next_id += 1
    
    def get_task_list(self) -> str:
        """Get internal task list as markdown."""
        lines = ["## My Tasks", ""]
        for task in self._tasks:
            lines.append(task.to_markdown())
        return "\n".join(lines)
    
    # ----- STEP 5: EXECUTE -----
    
    def execute(self, task_id: str) -> Dict[str, Any]:
        """Step 5: Execute a task via agent."""
        task = next((t for t in self._tasks if t.id == task_id), None)
        if not task:
            return {"error": f"Task {task_id} not found"}
        
        # Would call actual agent here
        task.status = "running"
        
        return {
            "status": "executed",
            "task": task_id,
            "action": task.action,
            "agent": task.agent
        }
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks where dependencies are satisfied."""
        ready = []
        for task in self._tasks:
            if task.status != "pending":
                continue
            deps_done = all(
                any(t.id == dep and t.status == "done" for t in self._tasks)
                for dep in task.depends_on
            )
            if deps_done:
                ready.append(task)
        return ready
    
    # ----- PROJECTTODO -----
    
    def get_project_context(self) -> Dict[str, Any]:
        """Get project context."""
        return self._project
    
    def update_project_progress(self, task_name: str):
        """Update project progress."""
        # Would update ProjectTODO.md
        pass
    
    def get_instructions(self) -> str:
        """Get system prompt."""
        return self._instructions



# Available agents
AGENTS = {
    "business_analyst": "src.agents.business_analyst.BusinessAnalystAgent",
    "database": "src.agents.database_agent.DatabaseAgent", 
    "coding": "src.integrations.coding_agent.wrapper.CodingAgentWrapper",
    "deep_search": "src.agents.deep_search.DeepSearchAgent",
    "architect": "src.agents.architect_agent.ArchitectAgent",
    "browser": "src.agents.browser_agent.BrowserAgent",
    "validator": "src.agents.validator_agent.ValidatorAgent",
}
