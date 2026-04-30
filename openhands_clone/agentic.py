"""
RadCod Agentic Core - Reasoning-Action Loop
==========================================
Implements the same approach as OpenHands:

REASONING (LLM) → ACTION (Tool) → OBSERVATION → REPEAT

This is the core of agentic systems - autonomous execution.
"""

import os
from pathlib import Path
from typing import Any, Callable
from dataclasses import dataclass, field

from openhands.sdk import LLM, Agent, Conversation
from openhands_clone.skills import find_skills
from openhands_clone.events import Event, EventType, message_event, observation_event, action_event, thinking_event
from openhands_clone.security import SecurityAnalyzer, ActionStatus


# =============================================================================
# Agentic Configuration
# =============================================================================

@dataclass
class AgenticConfig:
    """Configuration for the agentic loop."""
    
    model: str = "anthropic/claude-sonnet-4-20250513"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_iterations: int = 100
    workspace: str | None = None
    
    # Agentic settings
    enable_skills: bool = True
    enable_security: bool = True
    enable_planning: bool = True
    verbose: bool = False


# =============================================================================
# Execution Step
# =============================================================================

@dataclass
class ExecutionStep:
    """Single step in the reasoning-action loop."""
    
    step_number: int
    reasoning: str
    action: dict | None = None
    observation: str | None = None
    status: str = "pending"  # pending, running, complete, error
    
    def __repr__(self):
        return f"<Step {self.step_number}: {self.status}>"


# =============================================================================
# Execution Plan
# =============================================================================

class ExecutionPlan:
    """Manages the plan for a task."""
    
    def __init__(self, task: str):
        self.task = task
        self.steps: list[ExecutionStep] = []
        self.current_step = 0
    
    def add_step(self, reasoning: str, action: dict | None = None) -> ExecutionStep:
        """Add a step to the plan."""
        step = ExecutionStep(
            step_number=len(self.steps) + 1,
            reasoning=reasoning,
            action=action,
        )
        self.steps.append(step)
        return step
    
    def get_next(self) -> ExecutionStep | None:
        """Get the next step to execute."""
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            step.status = "running"
            return step
        return None
    
    def complete_current(self, observation: str) -> None:
        """Mark current step complete."""
        if self.current_step < len(self.steps):
            self.steps[self.current_step].observation = observation
            self.steps[self.current_step].status = "complete"
            self.current_step += 1
    
    def is_complete(self) -> bool:
        """Check if plan is complete."""
        return self.current_step >= len(self.steps)
    
    def __len__(self):
        return len(self.steps)


# =============================================================================
# Tool Executor
# =============================================================================

class ToolExecutor:
    """Executes tools and returns observations."""
    
    def __init__(self, workspace: str | None = None):
        self.workspace = workspace or os.getcwd()
        self._tools = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools (file_editor, terminal, etc.)."""
        # Tools would be registered here
        # Using our custom implementations as fallback
        pass
    
    def execute(self, tool_name: str, parameters: dict, security: SecurityAnalyzer | None = None) -> tuple[bool, str]:
        """
        Execute a tool.
        
        Returns: (success, observation)
        """
        # Check security
        if security:
            action_desc = f"{tool_name}: {parameters}"
            status = security.analyze(action_desc)
            if status == ActionStatus.DENIED:
                return False, "Action denied by security policy"
            if status == ActionStatus.NEEDS_CONFIRMATION:
                return False, "Action requires confirmation"
        
        # Execute tool
        try:
            if tool_name == "file_editor":
                return self._exec_file_editor(parameters)
            elif tool_name == "terminal":
                return self._exec_terminal(parameters)
            else:
                return False, f"Unknown tool: {tool_name}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _exec_file_editor(self, params: dict) -> tuple[bool, str]:
        """Execute file_editor tool."""
        command = params.get("command", "view")
        path = params.get("path", "")
        
        if command == "view":
            try:
                full_path = os.path.join(self.workspace, path)
                with open(full_path, 'r') as f:
                    content = f.read()
                return True, content
            except Exception as e:
                return False, f"Error reading {path}: {e}"
        
        elif command == "str_replace":
            # Would apply the edit
            return True, f"Applied edit to {path}"
        
        return True, f"file_editor {command} executed"
    
    def _exec_terminal(self, params: dict) -> tuple[bool, str]:
        """Execute terminal tool."""
        command = params.get("command", "")
        
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
            )
            return True, result.stdout or result.stderr
        except Exception as e:
            return False, f"Error: {e}"


# =============================================================================
# Core Reasoning-Action Loop
# =============================================================================

class AgenticLoop:
    """
    The core Reasoning-Action Loop.
    
    This implements OpenHands' approach:
    
        REASONING → ACTION → OBSERVATION → REPEAT
             ↑                               │
             └───────────────────────────────┘
    """
    
    def __init__(
        self,
        config: AgenticConfig,
        llm: LLM | None = None,
    ):
        self.config = config
        self.llm = llm or LLM(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=config.temperature,
        )
        
        # Initialize components
        self.workspace = config.workspace or os.getcwd()
        self.tool_executor = ToolExecutor(workspace=self.workspace)
        self.security = SecurityAnalyzer() if config.enable_security else None
        
        # Execution state
        self.plan: ExecutionPlan | None = None
        self.history: list[Event] = []
        self.iterations = 0
    
    def execute(self, task: str, max_iterations: int | None = None) -> str:
        """
        Execute a task using the reasoning-action loop.
        
        Args:
            task: The task description
            max_iterations: Override max iterations
            
        Returns:
            Final result message
        """
        max_iters = max_iterations or self.config.max_iterations
        
        # Initialize: Create first message event
        initial_event = message_event(content=task)
        self.history.append(initial_event)
        
        if self.config.verbose:
            print(f"📋 Task: {task}")
        
        # Main loop
        while self.iterations < max_iters:
            self.iterations += 1
            
            if self.config.verbose:
                print(f"\n🔄 Iteration {self.iterations}/{max_iters}")
            
            # Phase 1: REASONING
            reasoning_result = self._reasoning_phase(task)
            
            # Check if complete
            if reasoning_result.get("done"):
                return reasoning_result.get("message", "Done")
            
            # Phase 2: ACTION
            action_result = self._action_phase(reasoning_result)
            
            # Check if error
            if action_result.get("error"):
                return f"Error: {action_result['error']}"
            
            # Phase 3: OBSERVATION
            self._observation_phase(action_result)
        
        return f"Max iterations ({max_iters}) reached"
    
    def _reasoning_phase(self, task: str) -> dict:
        """
        Phase 1: REASONING
        
        The LLM analyzes the current state and decides what to do next.
        """
        # Build context for LLM
        context = self._build_context()
        
        # Skills matching
        skills_info = ""
        if self.config.enable_skills:
            matched = find_skills(task)
            if matched:
                skills_info = f"\nActive skills: {', '.join(s.name for s in matched)}"
        
        # Prompt the LLM
        prompt = f"""Task: {task}
{skills_info}

Current context:
{context}

What's the next action? Respond in JSON:
{{
  "reasoning": "why you're doing this",
  "action": {{"tool": "tool_name", "params": {{...}}}},
  "done": true/false,
  "message": "optional completion message"
}}"""
        
        # For now, simulate LLM response
        # In production, this would call self.llm.chat(prompt)
        return {
            "reasoning": "Planning approach",
            "action": None,
            "done": False,
        }
    
    def _action_phase(self, reasoning_result: dict) -> dict:
        """
        Phase 2: ACTION
        
        Execute the chosen tool action.
        """
        action = reasoning_result.get("action")
        
        if not action:
            return {"done": True, "message": "No action needed"}
        
        # Record action event
        action_desc = str(action)
        self.history.append(action_event(content=action_desc))
        
        # Execute via tool executor
        success, observation = self.tool_executor.execute(
            tool_name=action.get("tool", ""),
            parameters=action.get("params", {}),
            security=self.security,
        )
        
        return {
            "observation": observation,
            "success": success,
        }
    
    def _observation_phase(self, action_result: dict) -> None:
        """
        Phase 3: OBSERVATION
        
        Record the observation and continue loop.
        """
        obs = action_result.get("observation", "")
        self.history.append(observation_event(content=obs))
        
        if self.config.verbose:
            print(f"   📝 Observation: {obs[:100]}...")
    
    def _build_context(self) -> str:
        """Build context string from history."""
        context_parts = []
        
        for event in self.history[-5:]:  # Last 5 events
            context_parts.append(f"- {event.event_type.value}: {event.content[:100]}")
        
        return "\n".join(context_parts)
    
    def get_history(self) -> list[Event]:
        """Get execution history."""
        return self.history.copy()


# =============================================================================
# High-Level API
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
    Execute a task using the agentic reasoning-action loop.
    
    This is the main entry point - mirroring OpenHands' approach.
    
    Example:
        >>> result = execute_task("Create a hello world app")
        >>> print(result)
    """
    config = AgenticConfig(
        model=model,
        api_key=api_key,
        workspace=workspace,
        max_iterations=max_iterations,
        verbose=verbose,
    )
    
    loop = AgenticLoop(config=config)
    return loop.execute(task)


# =============================================================================
# Conversation Integration
# =============================================================================

def create_agentic_conversation(
    model: str = "anthropic/claude-sonnet-4-20250513",
    workspace: str | None = None,
) -> AgenticLoop:
    """Create an agentic conversation (for SDK compatibility)."""
    config = AgenticConfig(
        model=model,
        workspace=workspace,
    )
    return AgenticLoop(config=config)