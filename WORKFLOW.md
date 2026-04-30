# OpenHands Agentic Workflow - Deep Dive

## Practical Example: "Refactor this function to be async"

When user gives a coding task, here's the complete execution flow:

---

## 1. USER INPUT → MESSAGE

```
User: "Refactor calculate() to be async"
         ↓
   MessageEvent(type=user, content="Refactor calculate() to be async")
```

---

## 2. AGENT REASONING LOOP

```
┌─────────────────────────────────────────────────────────────┐
│                   REASONING PHASE                         │
│  ┌───────────────────────────────────────────────┐      │
│  │  1. Parse intent                            │      │
│  │     -> "refactor" + "async" = use Refactor   │      │
│  │        + PlanningSkill                      │      │
│  │                                      │      │
│  │  2. Check skills                        │      │
│  │     -> find_skills(user_input)            │      │
│  │     -> [PlanningSkill, RefactorSkill]   │      │
│  │                                      │      │
│  │  3. Create plan                        │      │
│  │     Step 1: Read current function      │      │
│  │     Step 2: Analyze async patterns   │      │
│  │     Step 3: Rewrite with async/await   │      │
│  │     Step 4: Write back                 │      │
│  │     Step 5: Verify                    │      │
│  └───────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   ACTION PHASE                              │
│  ┌───────────────────────────────────────────────┐      │
│  │  ACTION: tool_call                             │      │
│  │  name: "file_editor"                           │      │
│  │  parameters:                                  │      │
│  │    command: "view"                            │      │
│  │    path: "utils.py"                           │      │
│  └───────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. TOOL EXECUTION

```
file_editor.view("utils.py")
         ↓
┌──────────────────────────────────────────────────────────────┐
│                    WORKSPACE                                │
│  - Read file from filesystem                               │
│  - Return content to agent                                 │
└──────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────┐
│                   OBSERVATION                               │
│  ObservationEvent(                                         │
│    content="def calculate(x): ..."                         │
│  )                                                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. SECOND REASONING LOOP

```
Thinking: Now I see the function. It's:
  def calculate(x):
    return x * 2

Need to add async:
  async def calculate(x):
    await asyncio.sleep(0.1)  # Simulate async
    return x * 2
         ↓
ACTION: tool_call
  name: "file_editor"
  parameters:
    command: "str_replace"
    path: "utils.py"
    old_str: "def calculate(x):\n    return x * 2"
    new_str: "async def calculate(x):\n    await asyncio.sleep(0.1)\n    return x * 2"
```

---

## 5. SECURITY CHECK (Phase 2)

```
SecurityAnalyzer.analyze(action)
         ↓
ActionClassifier.classify("str_replace utils.py")
         ↓
SecurityLevel.LOW (file write, not destructive)
         ↓
ActionStatus.APPROVED
```

---

## 6. TOOL EXECUTION

```
file_editor.str_replace(...)
         ↓
Write to filesystem
         ↓
ObservationEvent(
  content="Updated: utils.py"
)
```

---

## 7. VERIFICATION

```
Thinking: Let me verify the change worked.
         ↓
ACTION: tool_call
  name: "file_editor"  
  command: "view"
  path: "utils.py"
         ↓
Verification: ✅ Function now has "async def"
```

---

## 8. COMPLETION

```
Final message to user:
"✅ Refactored calculate() to be async:
  - Added 'async' keyword
  - Added await asyncio.sleep(0.1) for simulation
  - Function now returns a coroutine"
```

---

## Complete Execution Log

```
MessageEvent(user="Refactor calculate() to be async")
  ↓
ThinkingEvent(plan: [read, analyze, rewrite, write, verify])
  ↓
ActionEvent(tool=file_editor.view)
  ↓
ObservationEvent(content="def calculate(x): ...")
  ↓
ThinkingEvent(need to add async keyword)
  ↓
ActionEvent(tool=file_editor.str_replace)
  ↓
SecurityAnalyzer: APPROVED
  ↓
ObservationEvent(content="Updated: utils.py")
  ↓
FinalResponse(msg)
```

---

## Key Components Explained

| Component | Role |
|-----------|------|
| **Conversation** | Orchestrates the entire flow |
| **Agent** | Reasoning-action loop engine |
| **LLM** | Generates reasoning & actions |
| **Tools** | file_editor, Terminal, Browser |
| **EventSystem** | Tracks all events |
| **SecurityAnalyzer** | Validates actions |
| **SkillRegistry** | Adds domain expertise |
| **Workspace** | File system access |

---

## Code Structure

```python
# How the conversation runs
convo = coding_agent()
convo.send_message("Refactor calculate() to be async")
convo.run()

# What happens internally:
# 1. conversation.send_message()
# 2. agent.run() loops:
#    a. llm.chat(history)
#    b. Parse response → action
#    c. SecurityAnalyzer.check(action)
#    d. tool.execute(action)
#    e. observation → history
#    f. repeat until done
# 3. Return result
```

---

## Key Insight: The Loop

```
┌──────────────┐     ┌──────────────┐
│  REASONING   │────▶│   ACTION    │
│  (LLM)       │     │  (Tool)     │
└──────────────┘     └──────────────┘
        ▲                    │
        │    OBSERVATION      │
        └────────────────────┘
```

- **Reasoning**: LLM decides what to do
- **Action**: Tool executes the plan
- **Observation**: Tool returns result
- **Loop repeats** until task complete