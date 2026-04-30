"""
OpenHands-Clone Skills
=====================
Skill system for the coding agent.

Skills add specialized behaviors and domain knowledge to the agent.
"""

import os
from pathlib import Path
from typing import Any


# =============================================================================
# Skill Base Classes
# =============================================================================

class Skill:
    """Base class for skills."""
    
    name: str = "base"
    description: str = "Base skill"
    triggers: list[str] = []
    
    def __init__(self, **kwargs):
        self.config = kwargs
    
    def get_prompt(self) -> str:
        """Get the skill prompt."""
        return self.description
    
    def should_activate(self, message: str) -> bool:
        """Check if skill should activate for message."""
        return any(trigger in message.lower() for trigger in self.triggers)


# =============================================================================
# Built-in Skills
# =============================================================================

class CodeReviewSkill(Skill):
    """Skill for code review."""
    
    name = "code-review"
    description = """
You are a code review expert. Review code for:
- Security vulnerabilities
- Performance issues
- Code quality and style
- Best practices
- Potential bugs

Provide actionable feedback with specific suggestions.
"""
    triggers = ["review", "code review", "review code", "critique"]


class DebugSkill(Skill):
    """Skill for debugging."""
    
    name = "debug"
    description = """
You are a debugging expert. When helping debug:
- Ask for error messages and stack traces
- Identify the root cause, not symptoms
- Suggest minimal reproducible examples
- Provide fix with explanation

Focus on finding the actual problem, not treating symptoms.
"""
    triggers = ["debug", "fix", "bug", "error", "issue", "broken"]


class RefactorSkill(Skill):
    """Skill for code refactoring."""
    
    name = "refactor"
    description = """
You are a refactoring expert. When refactoring:
- Maintain all existing functionality
- Make minimal changes
- Keep code simple and readable
- Follow SOLID principles
- Add docs for complex logic

Aim for clarity over cleverness.
"""
    triggers = ["refactor", "clean up", "simplify", "improve"]


class TestSkill(Skill):
    """Skill for testing."""
    
    name = "test"
    description = """
You are a testing expert. Write tests that:
- Cover edge cases
- Use descriptive names
- Test one thing at a time
- Are independent and isolated
- Follow AAA pattern (Arrange, Act, Assert)

Prioritize quality over quantity.
"""
    triggers = ["test", "spec", "assertion", "verify"]


class DocsSkill(Skill):
    """Skill for documentation."""
    
    name = "docs"
    description = """
You are a documentation expert. Write docs that:
- Explain why, not just what
- Include examples
- Stay in sync with code
- Are concise and clear
- Use standard formats

Good docs save time.
"""
    triggers = ["document", "docs", "readme", "comment"]


class SecuritySkill(Skill):
    """Skill for security."""
    
    name = "security"
    description = """
You are a security expert. Consider:
- Input validation
- Authentication/Authorization
- Data protection
- SQL injection, XSS, CSRF
- Secrets management

When in doubt, be paranoid.
"""
    triggers = ["security", "secure", "safe", "vulnerability"]


# =============================================================================
# Skill Registry
# =============================================================================

BUILT_IN_SKILLS: dict[str, type[Skill]] = {
    "code-review": CodeReviewSkill,
    "debug": DebugSkill,
    "refactor": RefactorSkill,
    "test": TestSkill,
    "docs": DocsSkill,
    "security": SecuritySkill,
}


def get_skill(name: str, **config) -> Skill:
    """Get a skill by name."""
    skill_class = BUILT_IN_SKILLS.get(name)
    if skill_class:
        return skill_class(**config)
    raise ValueError(f"Unknown skill: {name}")


def list_skills() -> list[str]:
    """List all available skills."""
    return list(BUILT_IN_SKILLS.keys())


def load_skills_from_dir(path: str | Path) -> list[Skill]:
    """Load skills from a directory."""
    skills = []
    path = Path(path)
    
    if not path.exists():
        return skills
    
    for file in path.glob("*.md"):
        # Simple skill loading from markdown
        content = file.read_text()
        skill = Skill(
            name=file.stem,
            description=content,
        )
        skills.append(skill)
    
    return skills