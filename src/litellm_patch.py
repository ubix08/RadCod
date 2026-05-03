"""
Litellm patch for NVIDIA NIM endpoints.
Automatically detects and routes to nvidia_nim provider.
"""

def patch_litellm():
    """Patch litellm to auto-detect NVIDIA endpoints."""
    import os
    import litellm
    from litellm import main as litellm_main
    from litellm.main import completion as litellm_completion
    
    # NOTE: NVIDIA_API_KEY must be set in environment by user
    # Do NOT hardcode API keys
    
    # Store original
    original_completion = litellm_completion
    
    def patched_completion(*args, **kwargs):
        """Patched completion that auto-detects NVIDIA endpoints."""
        model = kwargs.get('model', args[0] if args else '')
        
        # Auto-detect nvidia endpoint by model name
        is_nvidia_model = model and any(x in model.lower() for x in ['llama', 'mixtral', 'nemotron', 'minimax', 'z-ai', 'glm'])
        
        if is_nvidia_model and model:
            # Add meta prefix for llama models only (not minimax, z-ai, glm which already have vendor prefix)
            if 'meta/llama' in model.lower() or model.startswith('llama-'):
                if not model.startswith('meta/') and '/' not in model:
                    kwargs['model'] = f"meta/{model}"
            
            # Also set provider for NVIDIA endpoint
            if 'custom_llm_provider' not in kwargs:
                kwargs['custom_llm_provider'] = 'nvidia_nim'
        
        # Call original
        result = original_completion(*args, **kwargs)
        
        # Fix: populate content from reasoning_content if empty
        # Some models (minimax, z-ai, glm) only return reasoning_content
        try:
            msg = result.choices[0].message
            if msg.content is None and msg.reasoning_content:
                # Build a new message dict and reconstruct
                msg_dict = msg.model_dump()
                if not msg_dict.get('content'):
                    msg_dict['content'] = msg.reasoning_content
                # Reconstruct the message
                new_msg = type(msg).model_construct(**msg_dict)
                result.choices[0].message = new_msg
        except Exception as e:
            print(f'Patch warning: {e}')
        
        return result
    
    # Apply to the imported reference that SDK uses
    litellm_main.completion = patched_completion
    litellm.completion = patched_completion
    
    return patched_completion


def setup_nvidia_llm(model: str = None, api_key: str = None, api_base: str = None):
    """Create a properly configured LLM for NVIDIA."""
    import os
    patch_litellm()
    
    from openhands.sdk import LLM
    
    model = model or "meta/llama-3.1-70b-instruct"
    api_base = api_base or "https://integrate.api.nvidia.com/v1"
    
    # API key must come from environment
    api_key = api_key or os.environ.get('NVIDIA_API_KEY')
    if not api_key:
        raise ValueError("NVIDIA_API_KEY must be set in environment")
    
    return LLM(model=model, api_base=api_base, api_key=api_key)