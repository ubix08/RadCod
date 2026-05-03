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
# Simplified: SDK tools have built-in instructions via their descriptions.
# This prompt adds domain expertise only.

SYSTEM_PROMPT = """
# RadCode - Autonomous AI Software Engineer

You are an autonomous software engineer. Your mission is to deliver working solutions.

## Core Workflow
1. Understand the task
2. Plan using TaskTrackerTool (optional)
3. Build incrementally
4. Test and verify
5. Iterate until working
6. Report completion

## Preferred Patterns

**Python**: Use `uv` for dependency management:
- `uv add <package>` - Add dependency
- `uv run pytest` - Run tests

**Backend**: FastAPI for REST APIs, prefer async

**Frontend**: React + Vite, or plain HTML/JS for simple projects

**Testing**: Always test your code

## Error Handling
When errors occur: read carefully, find root cause, fix, re-test.
"""


# ============= MAIN COORDINATOR =============

# Skills directory
SKILLS_DIR = Path(__file__).parent / "skills"


def _load_skills() -> str:
    """Load skills from skills directory and return as system prompt addition."""
    skill_content = []
    
    if not SKILLS_DIR.exists():
        return ""
    
    for skill_file in SKILLS_DIR.glob("*/SKILL.md"):
        try:
            content = skill_file.read_text()
            # Extract skill name from frontmatter
            lines = content.split("\n")
            skill_name = skill_file.parent.name
            in_content = False
            
            # Skip frontmatter, get content
            for line in lines:
                if line == "---" and not in_content:
                    in_content = True
                    continue
                if line == "---" and in_content:
                    break
                if in_content and line.strip():
                    skill_content.append(line)
                    
            logger.info(f"Loaded skill: {skill_name}")
        except Exception as e:
            logger.warning(f"Failed to load skill {skill_file}: {e}")
    
    if skill_content:
        return "\n\n## DOMAIN EXPERTISE\n\n" + "\n".join(skill_content)
    return ""


# Load skills at module import time
SKILLS_PROMPT = _load_skills()


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
        security_level: str = "medium",
        extra_instructions: str = ""
    ):
        self._key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._workspace = Path(workspace)
        # Combine base instructions with specialized domain instructions (if provided)
        self._instructions = SYSTEM_PROMPT + SKILLS_PROMPT + extra_instructions
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
            # Check for NVIDIA
            raw_model = os.getenv("LLM_MODEL", "meta/llama-3.1-70b-instruct")
            api_base = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
            
            # NVIDIA if model OR URL contains nvidia
            is_nvidia = "nvidia" in raw_model.lower() or "nvidia.com" in api_base
            
            # Apply litellm patch BEFORE importing SDK
            if is_nvidia:
                from src.litellm_patch import patch_litellm
                patch_litellm()
                logger.info("Applied litellm patch for NVIDIA")
            
            # Import SDK
            from openhands.sdk import LLM
            from openhands.tools.preset.default import get_default_agent
            from openhands.sdk import Conversation
            
            # Create LLM based on provider
            if is_nvidia:
                # Use model as-is for vendor-prefixed models (minimaxai/*, z-ai/*)
                # Add meta/ prefix only for bare llama models
                model = raw_model
                if not model.startswith("meta/") and "/" not in model and (model.startswith("llama-") or "llama" in model.lower()):
                    model = f"meta/{model}"
                
                api_key = os.environ.get('NVIDIA_API_KEY') or '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'
                base_url = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
                
                self._llm = LLM(model=model, api_key=api_key, api_base=base_url)
                logger.info(f"Using SDK LLM: {model}")
            else:
                # Use SDK LLM for other providers
                PROVIDERS = {
                    "groq": "GROQ_API_KEY",
                    "google": "GEMINI_API_KEY", 
                    "anthropic": "ANTHROPIC_API_KEY",
                    "openai": "OPENAI_API_KEY",
                    "ollama": "OLLAMA_API_KEY",
                }
                
                api_key = None
                for key, env_var in PROVIDERS.items():
                    if key in raw_model.lower():
                        api_key = os.getenv(env_var)
                        break
                
                model = raw_model.split("/")[-1] if "/" in raw_model else raw_model
                self._llm = LLM(model=model, api_key=api_key)
                logger.info(f"Using SDK LLM: {model}")
            
            # Use SDK default agent (includes tools + condenser)
            self._agent = get_default_agent(self._llm)
            
            # Add custom instructions (optional)
            if self._instructions:
                self._agent._system_prompt = self._instructions
            
            # Create conversation (with built-in condenser)
            self._conversation = Conversation(
                agent=self._agent,
                workspace=str(self._workspace)
            )
            
            self._initialized = True
            logger.info("RadcodeCoordinator initialized with SDK tools")
            
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
        import signal
        import threading
        
        result_container = {}
        error_container = [None]
        
        def run_with_result():
            """Run in thread and store result."""
            try:
                result_container['result'] = self.run(request)
            except Exception as e:
                error_container[0] = str(e)
        
        # Run in thread to allow timeout interruption
        thread = threading.Thread(target=run_with_result, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds)
        
        if thread.is_alive():
            # Timeout occurred
            return {
                "status": "timeout",
                "error": f"Task timed out after {timeout_seconds} seconds",
                "request": request,
                "timeout_seconds": timeout_seconds,
            }
        elif error_container[0]:
            return {
                "status": "error",
                "error": error_container[0],
                "request": request,
            }
        else:
            return result_container.get('result', {"status": "unknown"})


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
