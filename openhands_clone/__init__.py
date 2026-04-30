"""
OpenHands-Clone - Phase 2 Complete
=============================
An optimized agentic coding system built with OpenHands SDK.

Phase 2: Events, Security, Condenser added.

Quick Start:
    from openhands_clone import coding_agent
    
    convo = coding_agent()
    convo.send_message("Create a simple hello world app")
    convo.run()

Phase 2 Features:
    - Events: Event system for tracking
    - Security: Action analysis & confirmation
    - Condenser: Context memory management
    - SkillRegistry with priorities

Phase 1 Features:
    - SDK core integration
    - 8 Skills with priorities
    - CLI interface
    - Persistence & metrics
"""

from openhands_clone.agent import (
    # Core classes
    CodingAgentConfig,
    CodingConversation,
    LLMConfig,
    # Builder
    coding_agent,
    create_coding_agent,
    # Constants
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_ITERATIONS,
    # SDK imports
    AgentSettings,
    ConversationSettings,
)

from openhands_clone.skills import (
    Skill,
    CodeReviewSkill,
    DebugSkill,
    RefactorSkill,
    TestSkill,
    DocsSkill,
    SecuritySkill,
    PlanningSkill,
    CritiqueSkill,
    SkillRegistry,
    get_skill,
    list_skills,
    find_skills,
    register_skill,
)

from openhands_clone.events import (
    Event,
    EventType,
    EventHistory,
    message_event,
    observation_event,
    action_event,
    thinking_event,
    error_event,
)

from openhands_clone.security import (
    SecurityAnalyzer,
    SecurityPolicy,
    SecurityLevel,
    ActionStatus,
    ActionClassifier,
    ConfirmationHandler,
)

from openhands_clone.condenser import (
    Condenser,
    SummarizingCondenser,
    CondenserSettings,
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
    "LLMConfig",
    "DEFAULT_MODEL",
    "DEFAULT_TEMPERATURE",
    "MAX_ITERATIONS",
    "AgentSettings",
    "ConversationSettings",
    # Skills
    "Skill",
    "SkillRegistry",
    "CodeReviewSkill",
    "DebugSkill",
    "RefactorSkill", 
    "TestSkill",
    "DocsSkill",
    "SecuritySkill",
    "PlanningSkill",
    "CritiqueSkill",
    "get_skill",
    "list_skills",
    "find_skills",
    "register_skill",
    # Events
    "Event",
    "EventType",
    "EventHistory",
    "message_event",
    "observation_event",
    "action_event",
    "thinking_event",
    "error_event",
    # Security
    "SecurityAnalyzer",
    "SecurityPolicy",
    "SecurityLevel",
    "ActionStatus",
    "ActionClassifier",
    "ConfirmationHandler",
    # Condenser
    "Condenser",
    "SummarizingCondenser",
    "CondenserSettings",
    # Sub-agents
    "SubAgent",
    "FunctionSubAgent",
    "delegate_parallel",
    "delegate_async",
    "delegate_sequential",
]

__version__ = "1.3.0"

# Agentic Loop
try:
    from openhands_clone.agentic import (
        AgenticConfig,
        AgenticLoop,
        ExecutionPlan,
        ExecutionStep,
        execute_task,
    )
    __all__.extend([
        "AgenticConfig",
        "AgenticLoop", 
        "ExecutionPlan",
        "execute_task",
    ])
except ImportError:
    pass

# Phase 3 additions
try:
    from openhands_clone.mcp import (
        MCPClient,
        MCPServer,
        MCPToolDefinition,
    )
    __all__.extend([
        "MCPClient",
        "MCPServer", 
        "MCPToolDefinition",
    ])
except ImportError:
    pass

try:
    from openhands_clone.workspace import (
        LocalWorkspace,
        RemoteWorkspace,
        AsyncRemoteWorkspace,
        create_workspace,
    )
    __all__.extend([
        "LocalWorkspace",
        "RemoteWorkspace", 
        "AsyncRemoteWorkspace",
        "create_workspace",
    ])
except ImportError:
    pass

try:
    from openhands_clone.observability import (
        Tracer,
        Span,
        Metrics,
        MetricsCollector,
        OTLPSExporter,
    )
    __all__.extend([
        "Tracer",
        "Span", 
        "Metrics",
        "MetricsCollector",
        "OTLPSExporter",
    ])
except ImportError:
    pass