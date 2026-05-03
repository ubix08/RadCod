---
name: code-review
description: Code review best practices, common issues, and review checklist.
triggers:
 - review
 - pr
 - pull request
 - merge
 - approve
---

# Code Review Expertise

## What to Look For

### Correctness
- Does the code do what it's supposed to?
- Are edge cases handled?
- Are there hidden bugs?

### Security
- No hardcoded secrets/keys
- Input validation
- SQL injection prevention
- XSS prevention

### Performance
- No unnecessary loops
- Efficient queries (DB)
- Proper caching

### Readability
- Clear variable names
- Comments on complex logic
- Consistent formatting

### Testing
- Tests cover new functionality
- Edge case tests
- Integration tests

## Review Checklist

- [ ] Code follows project style
- [ ] Tests pass
- [ ] No hardcoded secrets
- [ ] Error handling present
- [ ] Logging appropriate
- [ ] Docs updated (if needed)
- [ ] No commented-out code

## Comment Style

### Good Comments
```python
# Convert Unix timestamp to readable format
def format_time(ts):
    return datetime.fromtimestamp(ts)
```

### Bad Comments
```python
# Do the thing
def do_the_thing():  # Don't do this
    pass
```

## Approve vs Request Changes

### Approve When
- Code is correct and safe
- Minor suggestions can be addressed later
- Tests are adequate

### Request Changes When
- Bugs or security issues
- Missing tests
- Breaking changes without discussion

## Providing Feedback

- Be specific: "Line 42 - hardcoded API key"
- Suggest alternatives: "Consider using X instead"
- Ask questions: "Why did you choose this approach?"
- Be kind: Focus on code, not person