---
name: debugging
description: Systematic debugging approach, error analysis, and problem solving.
triggers:
 - error
 - bug
 - fix
 - debug
 - issue
 - fail
 - crash
 - exception
 - traceback
---

# Debugging Expertise

## Systematic Approach

### 1. Understand the Error

- Read the FULL error message
- Identify: What's the actual error? (not symptom)
- Note: File, line number, error type

### 2. Reproduce

- Can you consistently reproduce?
- What's the minimal reproduction?
- Log relevant values

### 3. Isolate

- Comment out code to narrow down
- Use binary search: "last working commit"
- Identify root cause

### 4. Fix

- Fix the ROOT cause
- Not symptoms
- Consider edge cases

### 5. Verify

- Does it fix the error?
- Are there new errors?
- Does it break existing tests?

## Common Error Patterns

### Python

| Error | Likely Cause |
|-------|-------------|
| `NameError` | Missing import/variable |
| `TypeError` | Wrong type passed |
| `AttributeError` | Wrong object type |
| `KeyError` | Missing dict key |
| `IndexError` | List index out of range |
| `ImportError` | Missing package |
| `SyntaxError` | Invalid Python syntax |

### JavaScript

| Error | Likely Cause |
|-------|-------------|
| `ReferenceError` | Undefined variable |
| `TypeError` | Wrong type |
| `SyntaxError` | Invalid syntax |
| `CORS` | Cross-origin issue |

## Debugging Tools

### Python
```bash
# Interactive debugger
python -m pdb script.py

# With prints
print(f"Debug: var={var}")

# Logging
import logging
logging.debug(f"var={var}")
```

### JavaScript
```javascript
// Console
console.log('Debug:', var);

// Browser dev tools
// F12 → Console / Network / Elements
```

## Logging Best Practices

```python
import logging
logger = logging.getLogger(__name__)

# Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.debug("Detailed info")
logger.info("General info") 
logger.warning("Warning")
logger.error("Error!")
```

## Testing Your Fix

1. Run the failing test
2. Apply fix
3. Re-run test - should pass
4. Run ALL tests - no regressions

## When Stuck

- Take a break (sleep on it)
- Explain the problem out loud
- Search the error message
- Check library docs/issues
- Ask for help