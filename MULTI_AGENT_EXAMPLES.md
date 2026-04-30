# RadCod Multi-Agent Execution Examples

> Complete examples showing planning → executing → verifying flow.

---

## Example 1: Refactor a Function

### Task
```
"Refactor the calculate() function in utils.py to be async"
```

### Full Pipeline Execution

```python
from openhands_clone.multi_agent import run_multipartite_task
from openhands_clone.repo_explorer import explore_repo

# First explore the repository
workspace = "/path/to/project"
analysis = explore_repo(workspace)

# Run through multi-agent pipeline
result = run_multipartite_task(
    task="Refactor the calculate() function in utils.py to be async",
    workspace=workspace,
)

print(result)
```

---

### Agent-by-Agent Breakdown

```
┌────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING AGENT                                          │
├────────────────────────────────────────────────────────────────────────────┤
│ Input: "Refactor calculate() to be async in utils.py"          │
│                                                                    │
│ Agent thinks:                                                      │
│ → First, I need to understand the codebase                       │
│ → Check what calculate() does                                     │
│ → Check how it's used throughout the code                          │
│ → Plan the refactor steps                                         │
│ → Identify risks                                                 │
│                                                                    │
│ STEPS:                                                            │
│ 1. Read utils.py to understand current function                  │
│ 2. Search for all uses of calculate()                            │
│ 3. Plan async conversion                                        │
│ 4. Execute changes                                              │
│ 5. Run tests to verify                                          │
│                                                                    │
│ Output: {                                                       │
│   "task": "Refactor calculate() to async",                      │
│   "plan": [                                                      │
│     {"step": 1, "action": "file_editor.view", "file": "utils.py"},│
│     {"step": 2, "action": "search", "pattern": "calculate\\("},   │
│     {"step": 3, "action": "edit", "changes": "add async"},       │
│     {"step": 4, "action": "run_tests"}                          │
│   ]                                                             │
│ }                                                               │
└────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTE AGENT                                            │
├────────────────────────────────────────────────────────────────────────┤
│ Step 1: file_editor.view("utils.py")                                     │
│ ────────────────────────                                           │
│ Output:                                                             │
│ ```                                                                │
│ def calculate(x):                                                  │
│     return x * 2                                                   │
│ ```                                                                │
│                                                                    │
│ Step 2: Search for all usages                                      │
│ ────────────────────────────                                       │
│ Found:                                                              │
│ - main.py: line 10  result = calculate(5)                          │
│ - api.py: line 23  value = calculate(data)                        │
│                                                                    │
│ Step 3: Apply changes                                             │
│ ───────────────────                                                │
│ Before:                                                             │
│ def calculate(x):                                                 │
│     return x * 2                                                   │
│                                                                    │
│ After:                                                              │
│ async def calculate(x):                                          │
│     await asyncio.sleep(0)  # Allow event loop                     │
│     return x * 2                                                  │
│                                                                    │
│ Also update callers:                                               │
│ - main.py: result = await calculate(5)                            │
│ - api.py: value = await calculate(data)                               │
│                                                                    │
│ Output: ✓ Changes applied successfully                               │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: VERIFY AGENT                                              │
├────────────────────────────────────────────────────────────────────────┤
│ Step 1: Run tests                                                 │
│ ─────────────────                                                 │
│ $ pytest                                                          │
│                                                                     │
│ test_calculate.py::test_basic PASSED                                  │
│ test_calculate.py::test_negative PASSED                          │
│ test_calculate.py::test_zero PASSED                              │
│                                                                     │
│ Output: ✓ All tests pass                                          │
│                                                                     │
│ Step 2: Check type hints (if any)                                 │
│ ─────────────────────────────────                               │
│ Output: ✓ No type checker issues                                │
│                                                                     │
│ Step 3: Verify no breakage                                       │
│ ─────────────────────────────────                                │
│ Output: ✓ All callers updated and working                       │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ FINAL RESULT                                                 │
├────────────────────────────────────────────────────────────────┤
│ {                                                              │
│   "task": "Refactor calculate() to async",                    │
│   "plan": "Created 4 steps",                                  │
│   "execution": {                                             │
│     "steps_executed": 4,                                      │
│     "results": [complete, complete, complete, complete]      │
│   },                                                          │
│   "verification": {                                           │
│     "changes_verified": 3,                                   │
│     "issues": [],                                            │
│     "status": "passed"                                       │
│   },                                                          │
│   "status": "complete"                                       │
│ }                                                             │
└────────────────────────────────────────────────────────────────┘
```

---

## Example 2: Add New Feature

### Task
```
"Add user authentication to the API"
```

### Full Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING AGENT                                              │
├─────────────────────────────────────────────────────────────────────┤
│ Input: "Add user authentication to the API"                          │
│                                                                      │
│ Steps:                                                               │
│ 1. Explore API structure                                            │
│ 2. Check existing auth (if any)                                     │
│ 3. Design auth system                                                │
│ 4. Implement endpoints                                              │
│ 5. Add middleware                                                   │
│ 6. Write tests                                                      │
│ 7. Documentation                                                    │
│                                                                      │
│ Plan: {                                                              │
│   "analysis": {                                                      │
│     "files": ["app.py", "routes/", "models/"],                      │
│     "framework": "FastAPI",                                          │
│     "existing_auth": "none"                                         │
│   },                                                                │
│   "steps": [                                                         │
│     {"step": 1, "action": "explore", "target": "API structure"},       │
│     {"step": 2, "action": "create", "file": "auth.py"},                │
│     {"step": 3, "action": "edit", "file": "app.py", "target": "router│
│     {"step": 4, "action": "create", "file": "migrations/"},            │
│     {"step": 5, "action": "test", "target": "auth"}                  │
│   ],                                                                │
│   "risks": [                                                         │
│     {"risk": "breaking changes", "level": "high"},                  │
│     {"risk": "security vulnerabilities", "level": "high"}              │
│   ]                                                                 │
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTE AGENT                                               │
├─────────────────────────────────────────────────────────────────────┤
│ Step 1: Explore                                                     │
│ - app.py: FastAPI app                                                │
│ - routes/: API endpoints                                             │
│ - No auth existing                                                 │
│                                                                      │
│ Step 2: Create auth.py                                              │
│ - User model                                                        │
│ - Password hashing (bcrypt)                                        │
│ - JWT token handling                                                │
│ - Login/logout endpoints                                            │
│                                                                      │
│ Step 3: Integrate with app.py                                       │
│ - Add auth router                                                   │
│ - Add JWT middleware                                               │
│ - Protect routes                                                    │
│                                                                      │
│ Step 4: Create migrations                                            │
│ - User table                                                        │
│                                                                      │
│ Step 5: Run tests                                                    │
│ - All auth tests pass                                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: VERIFY AGENT                                                │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Syntax: Correct                                                  │
│ ✓ Tests: 15 passed, 0 failed                                      │
│ ✓ Security:                                                       │
│   - Passwords properly hashed                                      │
│   - JWT secrets configurable                                       │
│   - SQL injection protected                                       │
│   - XSS protected                                                 │
│ ✓ Integration: All protected routes work                         │
│ ✓ Documentation: Updated                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Example 3: Bug Fix

### Task
```
"Fix the memory leak in data_processor.py"
```

### Full Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING AGENT                                              │
├─────────────────────────────────────────────────────────────────────┤
│ Input: "Fix memory leak in data_processor.py"                         │
│                                                                      │
│ Steps:                                                               │
│ 1. Analyze the file                                                 │
│ 2. Search for potential leak sources                                │
│ 3. Identify root cause                                            │
│ 4. Fix the issue                                                    │
│ 5. Verify fix                                                      │
│                                                                      │
│ Analysis techniques:                                               │
│ - Check for unclosed resources                                      │
│ - Check for growing collections                                     │
│ - Check for circular references                                   │
│ - Check for caching without limits                                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTE AGENT                                              │
├─────────────────────────────────────────────────────────────────────┤
│ Analysis findings:                                                  │
│ - Line 45: file opened, not closed                                │
│ - Line 78: dictionary grows without limit                        │
│ - Line 102: callback not removed                                  │
│                                                                      │
│ Fixes applied:                                                      │
│ 1. Added context manager for file                                 │
│ 2. Added LRU cache with max size                                    │
│ 3. Added cleanup callbacks                                         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: VERIFY AGENT                                                │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Fix works: No more memory growth                                │
│ ✓ Tests: All pass                                                 │
│ ✓ Edge cases: Handled                                            │
│                                                                      │
│ Result: MEMORY LEAK FIXED ✓                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Example 4: Complete Test Coverage

### Task
```
"Add test coverage to the payment module"
```

### Full Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING AGENT                      │
├─────────────────────────────────────────────────────────────────────┤
│ Steps:                                       │
│ 1. Explore payment module                │
│ 2. Analyze existing tests                 │
│ 3. Plan new tests                         │
│ 4. Write tests                           │
│ 5. Run coverage                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTE AGENT                       │
├─────────────────────────────────────────────────────────────────────┤
│ Module analysis:                          │
│ - PaymentProcessor class                 │
│ - 5 public methods                       │
│ - Edge cases to cover                    │
│                                          │
│ Tests written:                          │
│ - test_valid_payment                    │
│ - test_invalid_card                     │
│ - test_expired_card                    │
│ - test_insufficient_funds              │
│ - test_concurrent_payments             │
│ - test_refund                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: VERIFY AGENT                       │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Coverage: 85% → 95%                     │
│ ✓ All tests pass                         │
│ ✓ Edge cases covered                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Code Examples

### Python: Full Pipeline

```python
from openhands_clone.multi_agent import (
    create_planning_agent,
    create_executing_agent,
    create_verifying_agent,
)

workspace = "/path/to/project"

# Initialize agents
planner = create_planning_agent()
executor = create_executing_agent()
verifier = create_verifying_agent()

# Phase 1: Plan
print("Phase 1: Planning...")
plan = planner.create_plan("Refactor calculate() to async", workspace)
print(f"Created {len(plan['steps'])} steps")

# Phase 2: Execute  
print("Phase 2: Executing...")
results = executor.execute_plan(plan, workspace)
print(f"Executed {results['steps_executed']} steps")

# Phase 3: Verify
print("Phase 3: Verifying...")
verification = verifier.verify_changes(
    results['results'], 
    workspace
)
print(f"Status: {verification['status']}")

print(f"\nFinal: {verification['status']}")
```

### Python: Quick Single-Agent

```python
from openhands_clone import execute_task

# Simple - uses all agents automatically
result = execute_task(
    task="Add user authentication",
    workspace="/path/to/project",
    verbose=True,
)
print(result)
```

### CLI With Multi-Agent

```bash
# Uses agentic reasoning-action loop
radcod --agentic "Refactor calculate() to async"

# Full verbose mode
radcod --agentic --verbose "Add tests to payment module"
```

---

## Agent Communication Flow

```
Planning Agent Output:
{
  "task": "Refactor calculate()",
  "steps": [
    {"step": 1, "action": "view", "file": "utils.py"},
    {"step": 2, "action": "search", "pattern": "calculate("},
    {"step": 3, "action": "edit", "old": "...", "new": "..."},
    {"step": 4, "action": "test"}
  ],
  "files": ["utils.py", "main.py", "api.py"],
  "risks": ["async callers must be updated"]
}

Execute Agent Input:
← Receives plan from Planning Agent

Execute Agent Output:
{
  "completed_steps": 4,
  "results": [
    {"step": 1, "status": "complete", "output": "..."},
    {"step": 2, "status": "complete", "output": "..."},
    {"step": 3, "status": "complete", "output": "..."},
    {"step": 4, "status": "complete", "output": "..."}
  ]
}

Verify Agent Input:
← Receives results from Execute Agent

Verify Agent Output:
{
  "changes_verified": 3,
  "issues": [],
  "tests_passed": 15,
  "status": "passed"
}
```

---

## What Each Agent "Thinks"

### Planning Agent Reasoning

```
"I've been given a task to refactor code to be async.
First, I need to understand what calculate() does and how it's used.
Let me read the file and search for all callers.
I'll break this into specific steps:
1. Read the function
2. Find all usages
3. Plan the conversion
4. Execute changes
5. Update callers
6. Run tests to verify

I should flag:
- All callers need updating (risk: breaking changes)
- Tests need to handle asyncio (risk: test failures)"
```

### Execute Agent Reasoning

```
"I've received a plan with 4 steps.
Step 1: Read utils.py
- Let me see what calculate() does

Step 2: Find all usages
- Found 3 callers in main.py, api.py, tests/

Step 3: Apply async conversion  
- Simple function, easy to make async
- Need to add await points

Step 4: Test the changes
- Tests already use async where needed, good

I'm done. Passing to verifier."
```

### Verify Agent Reasoning

```
"I've received the execution results.
Let me verify thoroughly:
1. Syntax: ✓ No errors
2. Tests: ✓ All pass (12/12)
3. Integration: ✓ All callers work
4. Style: ✓ No linter warnings

Everything passes. I'll provide the summary."
```

---

*This shows exactly how planning, executing, and verifying agents work together in the multi-agent pipeline.*