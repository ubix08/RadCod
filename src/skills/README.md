# RadCode Skills

Skills provide specialized domain knowledge for the agent.

## Available Skills

| Skill | Trigger | Description |
|-------|---------|-----------|
| python-coding | python, pip, pytest | Python best practices |
| frontend-coding | react, vue, css, vite | Web frontend dev |
| backend-coding | api, fastapi, express | REST API dev |
| debugging | error, bug, fix, debug | Debugging approach |
| code-review | review, pr, merge | Code review |

## Usage

Skills are automatically loaded and triggered by keywords in the conversation.
The agent will use relevant skills when working on related tasks.

## Custom Skills

Add new skills in `src/skills/<skill-name>/SKILL.md`.

Format:
```markdown
---
name: skill-name
description: Brief description.
triggers:
 - keyword1
 - keyword2
---

# Skill Content

Your expertise content here...
```