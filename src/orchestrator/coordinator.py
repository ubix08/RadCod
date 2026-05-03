"""
Radcode Coordinator - Single Agent Architecture.

REFACTORED: One Agent that handles all tasks.
Uses TaskTrackerTool for subtask management.
Matches Devin's architecture: ONE agent that breaks tasks into subtasks.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("radcod.coordinator")

# ============= SYSTEM PROMPT =============

SYSTEM_PROMPT = """
# Radcode - Autonomous AI Software Engineer

You are an autonomous AI software engineer. Your role is to build complete applications from business requirements.

## Your Job

1. **Understand the request** - Read carefully what the user wants
2. **Plan your approach** - Use TaskTrackerTool to create subtasks
3. **Execute** - Use TerminalTool and FileEditorTool to build
4. **Verify** - Check your work
5. **Iterate** - Fix any issues

## Available Tools

### TaskTrackerTool
Use to track progress:
- Add subtasks for complex requests
- Mark tasks complete when done
- View pending tasks

### TerminalTool  
Execute commands:
- Install dependencies
- Run servers
- Run tests

### FileEditorTool
Write and edit code:
- Create files
- Read files
- Edit files

## Workflow

For "Build a CRM system":

1. Create project structure
2. Write database models
3. Write API endpoints
4. Write frontend
5. Test everything

Use TaskTrackerTool for every step.

## Important

- Be thorough - build complete applications
- Test your work
- Fix errors until it works
- Report completion when done
"""


# ============= COORDINATOR =============

class RadcodeCoordinator:
    """
    Single Agent Architecture - Matches Devin.
    
    ONE agent that:
    - Receives requests
    - Creates subtasks via TaskTrackerTool
    - Executes via TerminalTool/FileEditorTool
    """
    
    def __init__(self, api_key: str = None, workspace: str = "./workspace"):
        self._key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._workspace = Path(workspace)
        self._instructions = SYSTEM_PROMPT
        
        # SDK components - lazily initialized
        self._llm = None
        self._agent = None
        self._conversation = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize ONE SDK Agent."""
        if self._initialized:
            return
        
        try:
            from openhands.sdk import LLM, Agent, Conversation, Tool
            from openhands.tools.file_editor import FileEditorTool
            from openhands.tools.terminal import TerminalTool
            from openhands.tools.task_tracker import TaskTrackerTool
            
            # ONE LLM instance
            self._llm = LLM(
                model=os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929"),
                api_key=self._key,
                base_url=os.getenv("LLM_BASE_URL")
            )
            
            # ONE Agent with all tools
            self._agent = Agent(
                llm=self._llm,
                tools=[
                    Tool(name=TaskTrackerTool.name),
                    Tool(name=FileEditorTool.name),
                    Tool(name=TerminalTool.name),
                ],
                system_prompt=self._instructions
            )
            
            # ONE Conversation
            self._conversation = Conversation(
                agent=self._agent,
                workspace=str(self._workspace)
            )
            
            self._initialized = True
            logger.info("RadcodeCoordinator initialized (Single Agent)")
            
        except ImportError as e:
            logger.error(f"OpenHands SDK not installed: {e}")
            raise RuntimeError("openhands-sdk required. Install: pip install openhands-sdk openhands-tools")
    
    @property
    def agent(self) -> Any:
        """Get the SDK Agent."""
        self._initialize()
        return self._agent
    
    @property
    def conversation(self) -> Any:
        """Get the SDK Conversation."""
        self._initialize()
        return self._conversation
    
    def run(self, request: str) -> Dict[str, Any]:
        """
        Execute request using ONE Agent.
        
        The Agent handles:
        - Planning via TaskTrackerTool
        - Execution via TerminalTool/FileEditorTool
        """
        self._initialize()
        
        self._conversation.send_message(request)
        
        try:
            result = self._conversation.run()
            return {
                "status": "success",
                "result": result,
                "request": request
            }
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "request": request
            }
    
    # Backward compatibility
    def process_request(self, request: str) -> Dict[str, Any]:
        """Alias for run()."""
        return self.run(request)
    
    def analyze_only(self, request: str) -> Dict[str, Any]:
        """Legacy - just returns request info."""
        return {"request": request}
    
    def analyze(self, request: str) -> Dict[str, Any]:
        """Legacy - just returns request info."""
        return {"request": request}