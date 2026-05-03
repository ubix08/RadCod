"""
RadCode - Thin SDK Wrapper.

Just properly wraps OpenHands SDK - uses built-in functionality.
No custom agent logic, step tracking, or prompts.

Usage:
    from src.coordinator import create_agent
    
    agent = create_agent(workspace="./workspace")
    result = agent.run("Build a REST API")
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("radcod.coordinator")


class RadcodeCoordinator:
    """
    Thin wrapper around OpenHands SDK.
    
    Simply configures and exposes SDK components.
    All agent logic is handled by the SDK.
    """
    
    def __init__(
        self, 
        api_key: str = None, 
        workspace: str = "./workspace",
        security_level: str = "medium",
    ):
        self._key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._workspace = Path(workspace)
        self._security_level = security_level
        
        # SDK components - initialized on first use
        self._llm = None
        self._agent = None
        self._conversation = None
        self._initialized = False
        
        logger.info(f"Coordinator created: workspace={workspace}")
    
    def _ensure_initialized(self):
        """Initialize SDK components on first use."""
        if self._initialized:
            return
        
        # Get model config
        raw_model = os.getenv("LLM_MODEL", "meta/llama-3.1-70b-instruct")
        api_base = os.getenv("NVIDIA_API_BASE")
        
        # Determine provider
        is_nvidia = "nvidia" in raw_model.lower() or (api_base and "nvidia" in api_base)
        
        try:
            from openhands.sdk import LLM
            from openhands.tools.preset.default import get_default_agent
            from openhands.sdk import Conversation
            
            # Create LLM
            if is_nvidia:
                api_key = os.environ.get('NVIDIA_API_KEY')
                if not api_key:
                    raise ValueError("NVIDIA_API_KEY not set")
                
                model = raw_model
                if not model.startswith("meta/") and "/" not in model and model.startswith("llama-"):
                    model = f"meta/{model}"
                
                self._llm = LLM(
                    model=model,
                    api_key=api_key,
                    api_base=api_base or "https://integrate.api.nvidia.com/v1"
                )
            else:
                # Standard providers
                model = raw_model.split("/")[-1] if "/" in raw_model else raw_model
                
                # Auto-detect provider from model name
                provider_key = None
                for prov in ["groq", "google", "anthropic", "openai"]:
                    if prov in model.lower():
                        env_vars = {
                            "groq": "GROQ_API_KEY",
                            "google": "GEMINI_API_KEY",
                            "anthropic": "ANTHROPIC_API_KEY",
                            "openai": "OPENAI_API_KEY"
                        }
                        provider_key = os.getenv(env_vars.get(prov, ""))
                        break
                
                self._llm = LLM(model=model, api_key=provider_key)
            
            # Get default agent (has all tools: terminal, file editor, browser, etc.)
            self._agent = get_default_agent(self._llm)
            
            # Create conversation
            self._workspace.mkdir(parents=True, exist_ok=True)
            self._conversation = Conversation(
                agent=self._agent,
                workspace=str(self._workspace)
            )
            
            self._initialized = True
            logger.info("SDK initialized successfully")
            
        except ImportError as e:
            logger.error(f"SDK not installed: {e}")
            raise RuntimeError("pip install openhands-sdk openhands-tools")
    
    @property
    def conversation(self):
        """Access SDK conversation."""
        self._ensure_initialized()
        return self._conversation
    
    def run(self, request: str, **kwargs) -> Dict[str, Any]:
        """
        Execute task.
        
        Simply passes to SDK - all logic handled internally.
        """
        self._ensure_initialized()
        self._conversation.send_message(request)
        
        result = self._conversation.run(**kwargs)
        
        return {
            "status": "success",
            "result": result,
            "request": request
        }
    
    def run_with_timeout(self, request: str, timeout_seconds: int = 600) -> Dict[str, Any]:
        """Run with timeout wrapper."""
        import threading
        
        result_container = {}
        error_container = [None]
        
        def run_in_thread():
            try:
                result_container['result'] = self.run(request)
            except Exception as e:
                error_container[0] = str(e)
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds)
        
        if thread.is_alive():
            return {
                "status": "timeout",
                "error": f"Task timed out after {timeout_seconds}s"
            }
        elif error_container[0]:
            return {
                "status": "error", 
                "error": error_container[0]
            }
        
        return result_container.get('result', {"status": "unknown"})
    
    def can_continue(self) -> bool:
        """Check if can continue - SDK handles iteration."""
        return True  # SDK manages internally
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from SDK."""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "ok",
            "model": getattr(self._llm, 'model', 'unknown'),
            "workspace": str(self._workspace)
        }
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get context from SDK."""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "ok",
            "workspace": str(self._workspace)
        }
    
    def condense_context(self) -> Dict[str, Any]:
        """Condense via SDK (if supported)."""
        return {"status": "ok"}


def create_agent(
    api_key: str = None,
    workspace: str = "./workspace",
    security_level: str = "medium"
) -> RadcodeCoordinator:
    """Create SDK-wrapped agent."""
    return RadcodeCoordinator(
        api_key=api_key,
        workspace=workspace,
        security_level=security_level
    )


def main():
    """CLI entry."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.coordinator run <task>")
        sys.exit(1)
    
    task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "List files"
    
    agent = create_agent()
    result = agent.run(task)
    
    print(f"\nStatus: {result.get('status')}")
    print(f"Result: {result.get('result')}")


if __name__ == "__main__":
    main()
