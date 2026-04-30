"""
OpenHands-Clone
===============
An optimized agentic coding system built with OpenHands SDK.

Quick Start:
    from openhands_clone import coding_agent
    
    convo = coding_agent()
    convo.send_message("Create a simple hello world app")
    convo.run()

Features:
    - Core SDK: LLM, Agent, Conversation
    - Custom Tools: file_editor, terminal, task_tracker  
    - Skills: code-review, debug, refactor, test, docs, security
    - Sub-Agents: Parallel and sequential delegation
    - Streaming: Real-time response streaming
    - Persistence: Save and restore conversation state
    - Metrics: Token usage and cost tracking
"""

from openhands_clone.agent import (
    # Core classes
    CodingAgentConfig,
    CodingConversation,
    # Builder
    coding_agent,
    create_coding_agent,
    # Constants
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_ITERATIONS,
)

from openhands_clone.skills import (
    Skill,
    CodeReviewSkill,
    DebugSkill,
    RefactorSkill,
    TestSkill,
    DocsSkill,
    SecuritySkill,
    get_skill,
    list_skills,
    load_skills_from_dir,
)

from openhands_clone.subagents import (
    SubAgent,
    FunctionSubAgent,
    delegate_parallel,
    delegate_async,
    delegate_sequential,
)

__all__ = [
    # Agent
    "CodingAgentConfig",
    "CodingConversation", 
    "coding_agent",
    "create_coding_agent",
    "DEFAULT_MODEL",
    "DEFAULT_TEMPERATURE",
    "MAX_ITERATIONS",
    # Skills
    "Skill",
    "CodeReviewSkill",
    "DebugSkill",
    "RefactorSkill", 
    "TestSkill",
    "DocsSkill",
    "SecuritySkill",
    "get_skill",
    "list_skills",
    "load_skills_from_dir",
    # Sub-agents
    "SubAgent",
    "FunctionSubAgent",
    "delegate_parallel",
    "delegate_async",
    "delegate_sequential",
]

__version__ = "1.0.0"