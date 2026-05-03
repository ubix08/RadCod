"""
RadCode - Agent using litellm directly (avoids SDK version conflicts).

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


# ============= PROVIDER CONFIG =============

def detect_provider(model: str) -> Dict[str, Any]:
    """Auto-detect provider from model name."""
    model_lower = model.lower()
    
    # Model to provider mapping
    mappings = {
        # OpenRouter
        ("openrouter",): {
            "provider": "openrouter",
            "env_key": "OPENROUTER_API_KEY",
            "base_url": "https://openrouter.ai/api/v1"
        },
        # Groq (deprecated models)
        ("groq",): {
            "provider": "groq",
            "env_key": "GROQ_API_KEY",
            "base_url": "https://api.groq.com/openai/v1"
        },
        # NVIDIA
        ("nvidia", "minimax", "meta", "nemotron"): {
            "provider": "nvidia",
            "env_key": "NVIDIA_API_KEY",
            "base_url": "https://integrate.api.nvidia.com/v1"
        },
        # Google
        ("gemini",): {
            "provider": "google",
            "env_key": "GEMINI_API_KEY",
            "base_url": "https://generativelanguage.googleapis.com/v1"
        },
        # Anthropic
        ("claude", "sonnet", "haiku"): {
            "provider": "anthropic",
            "env_key": "ANTHROPIC_API_KEY",
            "base_url": None
        },
        # OpenAI
        ("gpt", "o1", "o3"): {
            "provider": "openai",
            "env_key": "OPENAI_API_KEY",
            "base_url": None
        },
    }
    
    # Check each prefix
    for prefixes, config in mappings.items():
        for prefix in prefixes:
            if prefix in model_lower:
                return {**config, "model": model}
    
    # Default to OpenRouter
    return {
        "provider": "openrouter",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "model": model
    }


class RadcodeCoordinator:
    """Agent using litellm directly."""
    
    def __init__(
        self, 
        api_key: str = None, 
        workspace: str = "./workspace",
        security_level: str = "medium",
    ):
        self._workspace = Path(workspace)
        self._security_level = security_level
        
        # Metrics
        self._prompt_tokens = 0
        self._completion_tokens = 0
        
        self._workspace.mkdir(parents=True, exist_ok=True)
        logger.info(f"Coordinator created: workspace={workspace}")
    
    def run(self, request: str, max_tokens: int = 2000, **kwargs) -> Dict[str, Any]:
        """Execute task using litellm."""
        # Get model
        model = os.getenv("LLM_MODEL", "openrouter/meta-llama/llama-3.1-70b-instruct")
        
        # Detect provider
        provider_config = detect_provider(model)
        api_key = os.environ.get(provider_config["env_key"])
        
        if not api_key:
            return {
                "status": "error",
                "error": f"{provider_config['env_key']} not set. Please configure your API key."
            }
        
        try:
            from litellm import completion
            
            # Build kwargs
            llm_kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": request}],
                "max_tokens": max_tokens,
            }
            
            # Add custom headers for OpenRouter
            if provider_config["provider"] == "openrouter":
                llm_kwargs["extra_headers"] = {
                    "HTTP-Referer": "https://radcod.dev",
                    "X-Title": "RadCode"
                }
            
            response = completion(**llm_kwargs)
            
            result_text = response.choices[0].message.content
            
            return {
                "status": "success",
                "result": result_text,
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
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics."""
        model = os.getenv("LLM_MODEL", "unknown")
        return {
            "status": "ok",
            "model": model,
            "workspace": str(self._workspace)
        }


def create_agent(
    api_key: str = None,
    workspace: str = "./workspace",
    security_level: str = "medium"
) -> RadcodeCoordinator:
    """Create agent."""
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
    
    if sys.argv[1] != "run":
        print("Usage: python -m src.coordinator run <task>")
        sys.exit(1)
    
    task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "List files"
    
    agent = create_agent()
    result = agent.run(task)
    
    print(f"\nStatus: {result.get('status')}")
    print(f"Result: {result.get('result')}")


if __name__ == "__main__":
    main()
