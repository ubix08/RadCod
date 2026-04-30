"""
OpenHands-Clone Agentic Coding System
=====================================
An optimized AI coding assistant built with the OpenHands SDK.

Features:
- LLM configuration with multiple provider support
- Agent with reasoning-action loop
- Conversation management
- Streaming and async support
- Metrics tracking
"""

import os
from pathlib import Path

# OpenHands SDK core imports - these work
from openhands.sdk import (
    LLM,
    Agent,
    Conversation,
)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_MODEL = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-20250513")
DEFAULT_TEMPERATURE = 0.7
MAX_ITERATIONS = 100


# =============================================================================
# Agent System Builder
# =============================================================================

class CodingAgentConfig:
    """Configuration for the coding agent."""
    
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_iterations: int = MAX_ITERATIONS,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.temperature = temperature
        self.max_iterations = max_iterations


def create_coding_agent(config: CodingAgentConfig) -> Agent:
    """
    Create an optimized coding agent with the OpenHands SDK.
    
    Args:
        config: Agent configuration
        
    Returns:
        Configured Agent instance
    """
    # Initialize LLM
    llm = LLM(
        model=config.model,
        api_key=config.api_key,
        base_url=config.base_url,
        temperature=config.temperature,
    )
    
    # Create agent with default tool set from SDK
    agent = Agent(
        llm=llm,
        max_iterations=config.max_iterations,
    )
    
    return agent


# =============================================================================
# Conversation Management
# =============================================================================

class CodingConversation:
    """
    High-level conversation manager for the coding agent.
    
    Provides:
    - Easy message sending
    - Persistence support
    - Streaming responses
    - Metrics tracking
    """
    
    def __init__(
        self,
        agent: Agent,
        workspace: str | Path | None = None,
    ):
        self.agent = agent
        self.workspace = workspace or os.getcwd()
        self.conversation = Conversation(
            agent=agent,
            workspace=str(self.workspace),
        )
    
    def send_message(self, message: str) -> None:
        """Send a message to the agent."""
        self.conversation.send_message(message)
    
    def run(self, streaming: bool = False) -> None:
        """Run the conversation to completion."""
        if streaming:
            for event in self.conversation.run(streaming=True):
                print(event, end="", flush=True)
        else:
            self.conversation.run()
    
    async def run_async(self) -> None:
        """Run the conversation asynchronously."""
        await self.conversation.run_async()
    
    def get_metrics(self) -> dict:
        """Get conversation metrics."""
        return self.conversation.get_metrics()
    
    def save_state(self, path: str | Path) -> None:
        """Save conversation state for persistence."""
        self.conversation.save_state(path)
    
    @classmethod
    def load_state(cls, path: str | Path, agent: Agent) -> "CodingConversation":
        """Load conversation state from file."""
        convo = cls(agent=agent)
        convo.conversation.load_state(path)
        return convo


# =============================================================================
# Builder Function
# =============================================================================

def coding_agent(
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    base_url: str | None = None,
    workspace: str | Path | None = None,
    max_iterations: int = MAX_ITERATIONS,
) -> CodingConversation:
    """
    Builder function to create a coding agent conversation.
    
    Example:
        >>> convo = coding_agent(
        ...     model="anthropic/claude-sonnet-4-20250513",
        ... )
        >>> convo.send_message("Create a simple web app")
        >>> convo.run()
    
    Args:
        model: LLM model identifier
        api_key: API key (reads from LLM_API_KEY if not provided)
        base_url: Custom base URL for LLM API
        workspace: Working directory for the agent
        max_iterations: Maximum agent iterations
        
    Returns:
        CodingConversation instance
    """
    config = CodingAgentConfig(
        model=model,
        api_key=api_key,
        base_url=base_url,
        max_iterations=max_iterations,
    )
    
    agent = create_coding_agent(config)
    
    return CodingConversation(
        agent=agent,
        workspace=workspace,
    )


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """CLI entry point for the coding agent."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="OpenHands-Clone Agentic Coding System"
    )
    parser.add_argument(
        "task",
        nargs="?",
        default="What can you help me with?",
        help="Task to give to the agent",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="LLM model to use",
    )
    parser.add_argument(
        "--workspace",
        default=os.getcwd(),
        help="Working directory",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=MAX_ITERATIONS,
        help="Maximum iterations",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream responses",
    )
    
    args = parser.parse_args()
    
    try:
        convo = coding_agent(
            model=args.model,
            workspace=args.workspace,
            max_iterations=args.max_iterations,
        )
        
        convo.send_message(args.task)
        
        if args.stream:
            convo.run(streaming=True)
        else:
            convo.run()
            
        print("\n" + "="*50)
        print("Metrics:", convo.get_metrics())
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()