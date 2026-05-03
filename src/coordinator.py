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
from typing import Any, Dict, Optional

logger = logging.getLogger("radcod.coordinator")


# ============= PROVIDER CONFIG =============

# Model to provider mapping
MODEL_PROVIDERS = {
    # NVIDIA models
    "nvidia": {
        "models": ["llama", "mixtral", "nemotron", "minimax", "glm", "qwen"],
        "env_key": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1"
    },
    # Anthropic
    "anthropic": {
        "models": ["claude", "sonnet", "haiku"],
        "env_key": "ANTHROPIC_API_KEY",
        "base_url": None
    },
    # OpenAI
    "openai": {
        "models": ["gpt-", "o1", "o3"],
        "env_key": "OPENAI_API_KEY",
        "base_url": None
    },
    # Google
    "google": {
        "models": ["gemini", "gemini-pro"],
        "env_key": "GEMINI_API_KEY",
        "base_url": None
    },
    # Groq
    "groq": {
        "models": ["llama", "mixtral", "gemma"],
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1"
    },
}


def detect_provider(model: str) -> Dict[str, Any]:
    """Auto-detect provider from model name."""
    model_lower = model.lower()
    
    for provider, config in MODEL_PROVIDERS.items():
        for model_prefix in config["models"]:
            if model_prefix in model_lower:
                return {
                    "provider": provider,
                    "env_key": config["env_key"],
                    "base_url": config.get("base_url"),
                    "model": model
                }
    
    # Default to Groq (free tier)
    return {
        "provider": "groq",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "model": model
    }


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
        
        # Metrics
        self._prompt_tokens = 0
        self._completion_tokens = 0
        
        logger.info(f"Coordinator created: workspace={workspace}")
    
    def _ensure_initialized(self):
        """Initialize SDK components on first use."""
        if self._initialized:
            return
        
        # Get model config
        raw_model = os.getenv("LLM_MODEL", "groq/llama-3.1-70b-instruct")
        
        # Detect provider
        provider_config = detect_provider(raw_model)
        api_key = os.environ.get(provider_config["env_key"])
        
        if not api_key:
            raise ValueError(f"{provider_config['env_key']} not set. Please configure your API key.")
        
        try:
            from openhands.sdk import LLM
            from openhands.tools.preset.default import get_default_agent
            from openhands.sdk import Conversation
            
            # Create LLM with provider config
            model = provider_config["model"]
            base_url = provider_config.get("base_url")
            
            # Handle NVIDIA specially
            if provider_config["provider"] == "nvidia":
                # Add meta prefix for bare llama models
                if "llama" in model.lower() and "/" not in model:
                    model = f"meta/{model}"
                if not base_url:
                    base_url = "https://integrate.api.nvidia.com/v1"
            
            # Create LLM
            llm_kwargs = {
                "model": model,
                "api_key": api_key
            }
            if base_url:
                llm_kwargs["api_base"] = base_url
            
            self._llm = LLM(**llm_kwargs)
            logger.info(f"LLM created: {model} via {provider_config['provider']}")
            
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
        
        try:
            result = self._conversation.run(**kwargs)
            
            # Try to get token usage if available
            try:
                if hasattr(self._llm, 'last_response'):
                    resp = self._llm.last_response
                    if hasattr(resp, 'usage'):
                        self._prompt_tokens = resp.usage.prompt_tokens
                        self._completion_tokens = resp.usage.completion_tokens
            except:
                pass
            
            return {
                "status": "success",
                "result": result,
                "request": request
            }
        except Exception as e:
            logger.error(f"Task failed: {e}")
            return {
                "status": "error",
                "error": str(e),
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
    
    @property
    def model(self) -> str:
        """Get current model."""
        return getattr(self._llm, 'model', 'unknown') if self._llm else 'unknown'
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from SDK."""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        total_tokens = self._prompt_tokens + self._completion_tokens
        # Estimate cost (approximate)
        cost = (self._prompt_tokens / 1_000_000 * 0.5) + (self._completion_tokens / 1_000_000 * 1.5)
        
        return {
            "status": "ok",
            "model": self.model,
            "workspace": str(self._workspace),
            "prompt_tokens": self._prompt_tokens,
            "completion_tokens": self._completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(cost, 6)
        }
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get context from SDK."""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "ok",
            "workspace": str(self._workspace),
            "model": self.model
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
