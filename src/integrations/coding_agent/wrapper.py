"""
Coding Agent Wrapper - OpenHands SDK Integration.

Wraps the OpenHands SDK for use in Radcod orchestrator.
"""

import os
import logging
from typing import Optional, Any

logger = logging.getLogger("radcod.coding_agent_wrapper")


class CodingAgentWrapper:
    """
    Wrapper for OpenHands SDK Agent.
    
    Uses the current OpenHands SDK pattern with LLM, Conversation, and Tools.
    """
    
    def __init__(
        self, 
        model_name: str = None,
        workspace_path: str = "./workspace",
        max_iterations: int = 50,
        api_key: str = None,
        base_url: str = None
    ):
        self.logger = logger
        self.workspace_path = workspace_path
        self.max_iterations = max_iterations
        
        # Resolve model - can be "openai/gpt-4o", "anthropic/claude-...", etc.
        self.model_name = model_name or os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        
        self.logger.info(f"Initializing CodingAgent with model: {self.model_name}")
        
        # Lazy init - only create when run_task is called
        self._agent = None
        self._conversation = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize the SDK components (lazy init)."""
        if self._initialized:
            return
            
        try:
            from openhands.sdk import LLM, Agent, Conversation, Tool
            from openhands.tools.file_editor import FileEditorTool
            from openhands.tools.terminal import TerminalTool
            
            # Create LLM
            self.llm = LLM(
                model=self.model_name,
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # Create agent with tools
            self._agent = Agent(
                llm=self.llm,
                tools=[
                    Tool(name=FileEditorTool.name),
                    Tool(name=TerminalTool.name),
                ]
            )
            
            # Create conversation
            self._conversation = Conversation(
                agent=self._agent, 
                workspace=self.workspace_path
            )
            
            self._initialized = True
            self.logger.info("CodingAgent initialized successfully.")
            
        except ImportError as e:
            self.logger.error(f"OpenHands SDK not installed: {e}")
            raise RuntimeError("openhands-sdk required. Install with: pip install openhands-sdk openhands-tools")
    
    def run_task(self, task: str) -> Any:
        """
        Execute a task using the agent.
        
        Args:
            task: The task description for the agent
            
        Returns:
            Result from agent execution
        """
        self.logger.info(f"Executing task: {task[:100]}...")
        
        try:
            self._initialize()
            
            # Run the agent on the task
            self._conversation.send_message(task)
            result = self._conversation.run()
            
            self.logger.info("Task completed successfully.")
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            raise e
    
    @property
    def agent(self):
        """Get the underlying agent."""
        self._initialize()
        return self._agent
