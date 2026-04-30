"""
RadCod Multi-Agent System
=========================
Maximal parity with OpenHands: Plan, Execute, Verify Agents.

Each agent has a specific role in the agentic pipeline.
"""

from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum

from openhands.sdk import LLM, Agent, Conversation


# =============================================================================
# Agent Types
# =============================================================================

class AgentType(Enum):
    """Types of agents in the system."""
    PLANNING = "planning"      # Break down tasks
    EXECUTING = "executing"   # Execute actions
    VERIFYING = "verifying"    # Verify results
    BROWSING = "browsing"     # Web browsing
    REVIEWING = "reviewing"    # Code review


# =============================================================================
# Agent Configuration
# =============================================================================

@dataclass
class AgentConfig:
    """Configuration for a specific agent type."""
    
    agent_type: AgentType
    model: str = "anthropic/claude-sonnet-4-20250513"
    temperature: float = 0.7
    max_iterations: int = 50
    tools: list[str] = field(default_factory=list)
    
    @classmethod
    def planning(cls, model: str = "anthropic/claude-sonnet-4-20250513") -> "AgentConfig":
        """Planning agent config."""
        return cls(
            agent_type=AgentType.PLANNING,
            model=model,
            temperature=0.3,  # More focused
            max_iterations=20,
        )
    
    @classmethod
    def executing(cls, model: str = "anthropic/claude-sonnet-4-20250513") -> "AgentConfig":
        """Executing agent config."""
        return cls(
            agent_type=AgentType.EXECUTING,
            model=model,
            temperature=0.7,
            max_iterations=100,
            tools=["file_editor", "terminal"],
        )
    
    @classmethod
    def verifying(cls, model: str = "anthropic/claude-sonnet-4-20250513") -> "AgentConfig":
        """Verifying agent config."""
        return cls(
            agent_type=AgentType.VERIFYING,
            model=model,
            temperature=0.5,
            max_iterations=30,
            tools=["file_editor", "terminal", "bash"],
        )
    
    @classmethod
    def browsing(cls, model: str = "anthropic/claude-sonnet-4-20250513") -> "AgentConfig":
        """Browsing agent config."""
        return cls(
            agent_type=AgentType.BROWSING,
            model=model,
            temperature=0.7,
            max_iterations=50,
            tools=["browser"],
        )


# =============================================================================
# Base Agent
# =============================================================================

class BaseCodingAgent:
    """Base class for all coding agents."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = LLM(
            model=config.model,
            temperature=config.temperature,
        )
        self.agent = Agent(
            llm=self.llm,
            max_iterations=config.max_iterations,
        )
        self.conversation: Conversation | None = None
        self._history: list[dict] = []
    
    def initialize(self, workspace: str) -> None:
        """Initialize agent with workspace."""
        self.conversation = Conversation(
            agent=self.agent,
            workspace=workspace,
        )
    
    def run(self, prompt: str) -> str:
        """Run the agent."""
        if not self.conversation:
            raise RuntimeError("Not initialized. Call initialize() first.")
        
        self.conversation.send_message(prompt)
        self.conversation.run()
        
        # Collect output
        return self._get_output()
    
    def _get_output(self) -> str:
        """Get conversation output."""
        # Would extract from conversation history
        return "Agent completed"


# =============================================================================
# Planning Agent
# =============================================================================

class PlanningAgent(BaseCodingAgent):
    """
    Planning Agent: Breaks down complex tasks into executable steps.
    
    Responsibilities:
    - Analyze the user's request
    - Understand the codebase structure
    - Create a detailed execution plan
    - Identify dependencies and risks
    """
    
    SYSTEM_PROMPT = """You are a Planning Agent. Your role is to break down complex tasks into clear, executable steps.

For each task:
1. UNDERSTAND the codebase - explore files to understand structure
2. ANALYZE requirements - what needs to be built/changed
3. CREATE steps - each step should be atomic and verifiable
4. IDENTIFY risks - what could go wrong

Output format for your plan:
```
## Plan
- Step 1: [Description]
  - Action: [tool to use]
  - Files: [files involved]
  - Risk: [low/medium/high]
- Step 2: ...
```

Be thorough but concise. Each step should be doable in one iteration."""
    
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig.planning())
    
    def create_plan(self, task: str, workspace: str) -> dict:
        """Create an execution plan for the task."""
        prompt = f"""{self.SYSTEM_PROMPT}

Task: {task}

Workspace: {workspace}

Create a detailed plan."""
        
        self.initialize(workspace)
        result = self.run(prompt)
        
        return {
            "task": task,
            "plan": result,  # Would parse into steps
            "status": "created",
        }
    
    def analyze_codebase(self, workspace: str) -> dict:
        """Analyze the codebase structure."""
        prompt = f"""Analyze this codebase:

1. What is the main purpose?
2. What are the key files and their roles?
3. What frameworks/libraries are used?
4. What is the directory structure?

Be thorough - explore multiple files."""
        
        self.initialize(workspace)
        result = self.run(prompt)
        
        return {
            "analysis": result,
            "status": "complete",
        }


# =============================================================================
# Execute Agent
# =============================================================================

class ExecuteAgent(BaseCodingAgent):
    """
    Execute Agent: Executes the planned actions.
    
    Responsibilities:
    - file_editor files (create, edit, refactor)
    - Run terminal commands
    - Make changes to the codebase
    - Handle errors and recover
    """
    
    SYSTEM_PROMPT = """You are an Execute Agent. Your role is to execute the planned actions precisely.

For each action:
1. UNDERSTAND the current state
2. MAKE the change precisely
3. VERIFY the change was applied
4. HANDLE any errors

Tools available:
- file_editor: Read, create, edit files
- terminal: Run commands

Always:
- Make minimal, focused changes
- Preserve existing functionality
- Add tests for new code
- Document your changes"""
    
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig.executing())
    
    def execute_plan(self, plan: dict, workspace: str) -> dict:
        """Execute a plan created by PlanningAgent."""
        steps = plan.get("steps", [])
        
        results = []
        for i, step in enumerate(steps):
            result = self._execute_step(step, workspace)
            results.append(result)
            
            if result.get("error"):
                break
        
        return {
            "steps_executed": len(results),
            "results": results,
            "status": "complete" if not results[-1].get("error") else "failed",
        }
    
    def _execute_step(self, step: dict, workspace: str) -> dict:
        """Execute a single step."""
        action = step.get("action", {})
        tool = action.get("tool")
        params = action.get("params", {})
        
        prompt = f"""Execute this step: {step.get('description')}

Tool: {tool}
Parameters: {params}

Execute precisely and report the result."""
        
        self.initialize(workspace)
        result = self.run(prompt)
        
        return {
            "step": step,
            "result": result,
            "status": "complete",
        }


# =============================================================================
# Verify Agent
# =============================================================================

class VerifyAgent(BaseCodingAgent):
    """
    Verify Agent: Verifies the executed changes.
    
    Responsibilities:
    - Run tests
    - Check for errors
    - Verify functionality
    - Validate code quality
    """
    
    SYSTEM_PROMPT = """You are a Verify Agent. Your role is to verify that executed changes are correct.

Verification checklist:
1. TESTS - Run existing tests, add new tests
2. SYNTAX - Check for syntax errors
3. LINT - Run linters
4. FORMAT - Check code formatting
5. DOCUMENTATION - Ensure docs are updated

Always be thorough - don't assume everything works.
Report ALL issues found."""
    
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig.verifying())
    
    def verify_changes(self, changes: list[dict], workspace: str) -> dict:
        """Verify a list of changes."""
        issues = []
        
        for change in changes:
            issue = self._verify_change(change, workspace)
            if issue:
                issues.append(issue)
        
        return {
            "changes_verified": len(changes),
            "issues": issues,
            "status": "passed" if not issues else "failed",
        }
    
    def _verify_change(self, change: dict, workspace: str) -> dict | None:
        """Verify a single change."""
        prompt = f"""Verify this change:

{change}

Run tests, check syntax, verify functionality.
Report any issues found."""
        
        self.initialize(workspace)
        result = self.run(prompt)
        
        if "error" in result.lower() or "failed" in result.lower():
            return {"change": change, "issue": result}
        
        return None
    
    def run_tests(self, workspace: str, test_pattern: str = "test*") -> dict:
        """Run tests in the workspace."""
        prompt = f"""Run tests matching: {test_pattern}

Execute: pytest {test_pattern} -v

Report:
- Tests passed/failed
- Any errors
- Coverage if available"""
        
        self.initialize(workspace)
        result = self.run(prompt)
        
        return {
            "test_result": result,
            "status": "complete",
        }


# =============================================================================
# Browsing Agent
# =============================================================================

class BrowsingAgent(BaseCodingAgent):
    """
    Browsing Agent: For web browsing and research.
    
    Responsibilities:
    - Search the web
    - Extract information
    - Research topics
    """
    
    SYSTEM_PROMPT = """You are a Browsing Agent. Your role is to find information on the web.

Tasks:
- Search documentation
- Find examples
- Research libraries/frameworks
- Extract technical details

Always cite your sources."""
    
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig.browsing())
    
    def search(self, query: str) -> dict:
        """Search for information."""
        prompt = f"""Research: {query}

Find:
- Relevant documentation
- Examples
- Best practices
- Common issues"""
        
        result = self.run(prompt)
        
        return {
            "query": query,
            "results": result,
            "status": "complete",
        }


# =============================================================================
# Reviewing Agent
# =============================================================================

class ReviewingAgent(BaseCodingAgent):
    """
    Reviewing Agent: For code review.
    
    Responsibilities:
    - Review code changes
    - Suggest improvements
    - Check for issues
    """
    
    SYSTEM_PROMPT = """You are a Reviewing Agent. Your role is to review code changes thoroughly.

Review checklist:
1. CORRECTNESS - Does it work as intended?
2. SECURITY - Any vulnerabilities?
3. PERFORMANCE - Any issues?
4. STYLE - Follows project conventions?
5. DOCUMENTATION - Are docs updated?
6. TESTS - Are tests adequate?

Provide specific, actionable feedback."""
    
    def review_code(self, code: str, context: str = "") -> dict:
        """Review code."""
        prompt = f"""Review this code:

```{code}```

Context: {context}

{self.SYSTEM_PROMPT}"""
        
        result = self.run(prompt)
        
        return {
            "review": result,
            "status": "complete",
        }


# =============================================================================
# Multi-Agent Pipeline
# =============================================================================

class MultiAgentPipeline:
    """
    The complete multi-agent pipeline mirroring OpenHands.
    
    orchestrator:
        ┌─────────────┐
        │  Planning  │ ──→ Plan
        │   Agent    │
        └─────────────┘
              │
              ▼
        ┌─────────────┐
        │ Executing  │ ──→ Execute
        │   Agent   │
        └─────────────┘
              │
              ▼
        ┌─────────────┐
        │ Verifying │ ──→ Verify
        │   Agent  │
        └─────────────┘
              │
              ▼
         Results + Report
    """
    
    def __init__(self, workspace: str, model: str = "anthropic/claude-sonnet-4-20250513"):
        self.workspace = workspace
        self.model = model
        
        # Initialize all agents
        self.planner = PlanningAgent(AgentConfig.planning(model))
        self.executor = ExecuteAgent(AgentConfig.executing(model))
        self.verifier = VerifyAgent(AgentConfig.verifying(model))
        self.reviewer = ReviewingAgent()
        
        # Results
        self.plan: dict = {}
        self.execution_results: list[dict] = []
        self.verification_results: dict = {}
    
    def run(self, task: str) -> dict:
        """Run the complete pipeline."""
        # Phase 1: Planning
        print("📋 Phase 1: Planning...")
        self.plan = self._planning_phase(task)
        
        # Phase 2: Execution
        print("🔨 Phase 2: Executing...")
        self.execution_results = self._executing_phase(self.plan)
        
        # Phase 3: Verification
        print("✅ Phase 3: Verifying...")
        self.verification_results = self._verifying_phase(self.execution_results)
        
        return self._compile_results()
    
    def _planning_phase(self, task: str) -> dict:
        """Phase 1: Create plan."""
        plan = self.planner.create_plan(task, self.workspace)
        
        # Also analyze codebase
        analysis = self.planner.analyze_codebase(self.workspace)
        plan["analysis"] = analysis
        
        return plan
    
    def _executing_phase(self, plan: dict) -> list[dict]:
        """Phase 2: Execute plan."""
        return self.executor.execute_plan(plan, self.workspace)
    
    def _verifying_phase(self, results: list[dict]) -> dict:
        """Phase 3: Verify results."""
        changes = [r.get("change", {}) for r in results]
        return self.verifier.verify_changes(changes, self.workspace)
    
    def _compile_results(self) -> dict:
        """Compile final results."""
        return {
            "task": self.plan.get("task"),
            "plan": self.plan,
            "execution": self.execution_results,
            "verification": self.verification_results,
            "status": self.verification_results.get("status"),
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_planning_agent(model: str = "anthropic/claude-sonnet-4-20250513") -> PlanningAgent:
    """Create a planning agent."""
    return PlanningAgent(AgentConfig.planning(model))


def create_executing_agent(model: str = "anthropic/claude-sonnet-4-20250513") -> ExecuteAgent:
    """Create an executing agent."""
    return ExecuteAgent(AgentConfig.executing(model))


def create_verifying_agent(model: str = "anthropic/claude-sonnet-4-20250513") -> VerifyAgent:
    """Create a verifying agent."""
    return VerifyAgent(AgentConfig.verifying(model))


def run_multipartite_task(task: str, workspace: str, model: str = "anthropic/claude-sonnet-4-20250513") -> dict:
    """Run a task through the complete multi-agent pipeline."""
    pipeline = MultiAgentPipeline(workspace=workspace, model=model)
    return pipeline.run(task)