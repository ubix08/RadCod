# RadCode Architecture - Devin Agentic Structure

## Overview

RadCode implements a **Devin-like autonomous software agent** built on OpenHands SDK. This document explains the architecture.

---

## Devin Agent Pattern

Devin is a **single autonomous agent** that:

```
┌─────────────────────────────────────────────────────────────┐
│                      Devin Agent                            │
├─────────────────────────────────────────────────────────────┤
│  1. REASON     → Uses LLM to think about the problem        │
│  2. PLAN       → Breaks down into steps                   │
│  3. ACT        → Uses tools to execute                    │
│  4. OBSERVE    → Sees tool results                      │
│  5. ITERATE    → Refines until done                     │
└─────────────────────────────────────────────────────────────┘
```

---

## OpenHands SDK Pattern (Underlying)

The SDK provides the core loop:

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenHands SDK                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   LLM                                                        │
│    │                                                        │
│    ▼                                                        │
│  Agent (reasoning-action loop)                                │
│    │                                                        │
│    ├── selects ──→ Tool (action)                          │
│    │                   │                                 │
│    │                   ▼                                 │
│    │              Executor                              │
│    │                   │                                 │
│    │                   ▼                                 │
│    │              Observation (result)               │
│    │                   │                                 │
│    └───────────────────┘                                │
│                    │                                     │
│                 (loop back)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## RadCode Components

### 1. RadcodeCoordinator (Main Agent)

**Purpose**: Single autonomous agent entry point

```python
from src.coordinator import RadcodeCoordinator

# Simple usage
coordinator = RadcodeCoordinator()
result = coordinator.run("Build a REST API")
```

**What it does**:
- Wraps OpenHands SDK `Conversation` + `Agent`
- Initializes LLM with multi-provider support
- Configures tools (Terminal, FileEditor, TaskTracker, Browser, Glob, Grep, TaskToolSet)
- Adds security analyzer
- Adds context condenser for long tasks
- Loads built-in sub-agents

**Internal structure**:
```python
RadcodeCoordinator
├── _llm: LLM                    # Language model
├── _agent: Agent                # SDK Agent (reasoning-action)
├── _conversation: Conversation # SDK Conversation
│   ├── condenser: LLMSummarizingCondenser
│   └── tools: [TerminalTool, FileEditorTool, ...]
└── run(request)
    └── conversation.run()
```

### 2. RadcodeAgent (Domain-Specific)

**Purpose**: Specialized agents for specific domains

```python
from src.agents import BackendAgent, FrontendAgent, TestAgent

# Use specialized agent
agent = BackendAgent()
result = agent.run("Create a user API")
```

**Types**:
- `BackendAgent` - API, database, server
- `FrontendAgent` - React, Vue, web UI
- `TestAgent` - Testing, QA
- `DevOpsAgent` - Deployment, Docker
- `CodeReviewAgent` - PR review

**What it does**:
- Wraps RadcodeCoordinator with domain-specific prompts
- Provides specialized system instructions

### 3. RadCodeOrchestrator (Multi-Agent)

**Purpose**: Complex task decomposition

```python
from src.orchestrator import RadCodeOrchestrator

orchestrator = RadCodeOrchestrator()
result = orchestrator.run("Build a full-stack CRM")
```

**What it does**:
- Decomposes complex task into subtasks
- Spawns agents for parallel execution
- Aggregates results

**Structure**:
```
RadCodeOrchestrator
├── decompose(task) → [SubTask1, SubTask2, ...]
├── spawn_agent(subtask) → RadcodeCoordinator
├── run_parallel(subtasks) → results
└── aggregate(results) → final_result
```

---

## When to Use Which

| Use Case | Component |
|----------|-----------|
| Simple task ("fix a bug") | `RadcodeCoordinator` |
| Domain task ("build API") | `BackendAgent` |
| Complex project ("build CRM") | `RadCodeOrchestrator` |

---

## Tool Sets

### Core Tools (All agents have)

| Tool | Purpose |
|------|--------|
| `TerminalTool` | Run commands |
| `FileEditorTool` | Read/write files |
| `TaskTrackerTool` | Manage subtasks |
| `BrowserToolSet` | Web browsing |

### Extended Tools (Available)

| Tool | Purpose |
|------|--------|
| `GlobTool` | File pattern matching |
| `GrepTool` | Content search |
| `TaskToolSet` | Sub-agent delegation |

---

## Execution Flow

```
User: "Create a calculator app"

    ┌─────────────────────────────────────┐
    │  RadcodeCoordinator.run()            │
    ├─────────────────────────────────────┤
    │  1. Initialize (if not done)        │
    │     - Create LLM                   │
    │     - Create Agent + Tools         │
    │     - Create Conversation        │
    │                                     │
    │  2. Send request                  │
    │     conversation.send_message()   │
    │                                     │
    │  3. Run loop                      │
    │     conversation.run()            │
    │     ┌──────────────────────┐      │
    │     │ Agent loop:          │      │
    │     │ 1. Think (LLM)      │      │
    │     │ 2. Select tool      │      │
    │     │ 3. Execute         │      │
    │     │ 4. Get result      │      │
    │     │ 5. Repeat          │      │
    │     └──────────────────────┘      │
    │                                     │
    │  4. Return result                │
    └─────────────────────────────────────┘
```

---

## Security Levels

| Level | Behavior |
|-------|----------|
| `high` | Block dangerous actions (AlwaysConfirm) |
| `medium` | Gray swan analysis (warn on risk) |
| `low` | Minimal blocking |

---

## Context Management

For long-running tasks:

- **Automatic**: `LLMSummarizingCondenser` truncates at 80 events
- **Manual**: `coordinator.condense_context()`
- **Check**: `coordinator.can_continue()`

---

## API Server

Start server:

```bash
python -m src.cli server --port 8000
```

Endpoints:
- `POST /run` - Execute task
- `GET /metrics` - Token usage
- `GET /context` - Context summary
- `POST /deploy` - Deploy project

---

## Summary

```
┌────────────────────────────────────────────────────────────┐
│                    RadCode                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   User Code                                         │──────│──► RadcodeCoordinator
│   (my script)                                       │      │      │
│                                                │      │      │ (Single Agent)
│   CLI                                            │      │      │
│   (python -m src.cli run)                         │──────│──────│
│                                                │      │      │
│   Server                                          │      │      │
│   (FastAPI)                                      │      │      │
│                                                │      │      │
│   ┌────────────────┬────────────────┐          │      │      │
│   │ /run           │ /orchestrator   │          │      │      │
│   │ (single)       │ (multi)         │          │      │──────│──► RadCodeOrchestrator
│   └────────────────┴────────────────┘          │      │      │ (Multi-Agent)
│                                                │      │      │
└────────────────────────────────────────────────────────────┘
```

The key components:
1. **RadcodeCoordinator** = Single Devin-like agent
2. **RadCodeOrchestrator** = Multi-agent for complex tasks
3. **RadcodeAgent** = Domain-specific wrapper (optional)