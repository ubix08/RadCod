"""
OpenHands-Clone Examples
=======================
Usage examples for the coding agent.
"""

# Example 1: Basic Usage
# --------------------
def example_basic():
    """Basic usage example."""
    from openhands_clone import coding_agent
    
    convo = coding_agent(
        model="anthropic/claude-sonnet-4-20250513",
    )
    convo.send_message("Write 3 facts about Python to FACTS.txt")
    convo.run()


# Example 2: With Custom Workspace
# ---------------------------
def example_workspace():
    """Custom workspace example."""
    from openhands_clone import coding_agent
    
    convo = coding_agent(
        workspace="/tmp/my-project",
    )
    convo.send_message("Create a simple Flask app")
    convo.run()


# Example 3: Streaming Responses
# -----------------------------
def example_streaming():
    """Streaming example."""
    from openhands_clone import coding_agent
    
    convo = coding_agent()
    convo.send_message("Count to 5")
    convo.run(streaming=True)


# Example 4: With Skills
# ---------------------
def example_with_skills():
    """Using skills example."""
    from openhands_clone import get_skill
    
    # Get a skill
    review_skill = get_skill("code-review")
    print(f"Skill: {review_skill.name}")
    print(f"Prompt: {review_skill.get_prompt()[:100]}...")


# Example 5: Persistence
# ----------------------
def example_persistence():
    """Persistence example."""
    from openhands_clone import coding_agent
    import tempfile
    
    # Create agent
    convo = coding_agent()
    convo.send_message("List files in current dir")
    convo.run()
    
    # Save state
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        convo.save_state(f.name)
        print(f"Saved to: {f.name}")


# Example 6: Metrics
# ------------------
def example_metrics():
    """Metrics example."""
    from openhands_clone import coding_agent
    
    convo = coding_agent()
    convo.send_message("Hello")
    convo.run()
    
    metrics = convo.get_metrics()
    print(f"Metrics: {metrics}")


# Example 7: Parallel Delegation
# -------------------------
def example_parallel():
    """Parallel sub-agent example."""
    from openhands_clone.subagents import (
        SubAgent,
        FunctionSubAgent,
        delegate_parallel,
    )
    
    # Create simple agents
    def task1(s: str) -> str:
        return f"Processed: {s}"
    
    def task2(s: str) -> str:
        return f"Analyzed: {s}"
    
    agents = [
        FunctionSubAgent("processor", task1),
        FunctionSubAgent("analyzer", task2),
    ]
    
    results = delegate_parallel(agents, ["data1", "data2"])
    for name, result in results:
        print(f"{name}: {result}")


# Example 8: Async Execution
# --------------------------
def example_async():
    """Async example."""
    import asyncio
    from openhands_clone import coding_agent
    
    async def main():
        convo = coding_agent()
        await convo.run_async()
    
    asyncio.run(main())


# Run all examples
if __name__ == "__main__":
    print("Running examples...")
    
    examples = [
        ("Basic", example_basic),
        ("Workspace", example_workspace),
        ("Skills", example_with_skills),
        ("Parallel", example_parallel),
    ]
    
    for name, func in examples:
        print(f"\n=== {name} ===")
        try:
            func()
        except Exception as e:
            print(f"Error: {e}")