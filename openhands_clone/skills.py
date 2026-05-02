"""
OpenHands-Clone Skills - Phase 1
=================================
Skill system for the coding agent.

Phase 1 Updates:
- SDK Skill integration where available
- Enhanced skill matching patterns
- Named skill variants

Skills add specialized behaviors and domain knowledge to the agent.
"""

import os
from pathlib import Path
from typing import Any

# Try SDK skill integration
try:
    from openhands.sdk.skill import Skill as SDKSkill
    HAS_SDK_SKILL = True
except ImportError:
    SDKSkill = object
    HAS_SDK_SKILL = False

# =============================================================================
# Skill Base Classes
# =============================================================================

class Skill(SDKSkill):
    """Base class for skills, inheriting from SDK Skill."""
    
    name: str = "base"
    description: str = "Base skill"
    triggers: list[str] = []
    priority: int = 0
    
    def __init__(self, **kwargs):
        super().__init__()
        self.config = kwargs
    
    def get_prompt(self) -> str:
        """Get the skill prompt."""
        return self.description
    
    def should_activate(self, message: str) -> bool:
        """Check if skill should activate for message."""
        return any(trigger in message.lower() for trigger in self.triggers)
    
    def __repr__(self) -> str:
        return f"<Skill: {self.name}>"


# =============================================================================
# Skill Registry
# =============================================================================

class SkillRegistry:
    """Registry for managing skills."""
    
    def __init__(self):
        self._skills: dict[str, Skill] = {}
    
    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill
    
    def get(self, name: str) -> Skill | None:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def find(self, message: str) -> list[Skill]:
        """Find skills that match a message."""
        matches = []
        for skill in self._skills.values():
            if skill.should_activate(message):
                matches.append(skill)
        return sorted(matches, key=lambda s: s.priority, reverse=True)
    
    def list_all(self) -> list[str]:
        """List all registered skills."""
        return list(self._skills.keys())


# Global registry
_registry = SkillRegistry()


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
    priority = 10


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
    triggers = ["debug", "fix", "bug", "error", "issue", "broken", "not working"]
    priority = 10


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
    triggers = ["refactor", "clean up", "simplify", "improve", "optimize"]
    priority = 5


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
    triggers = ["test", "spec", "assertion", "verify", "write tests"]
    priority = 5


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
    triggers = ["document", "docs", "readme", "comment", "explain"]
    priority = 3


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
    triggers = ["security", "secure", "safe", "vulnerability", "auth"]
    priority = 8


# New in Phase 1: Additional skills
class PlanningSkill(Skill):
    """Skill for planning."""
    
    name = "planning"
    description = """
You are a planning expert. Break down tasks:
- Understand requirements first
- List all steps needed
- Identify dependencies
- Estimate complexity
- Flag uncertainties early

Plan before coding.
"""
    triggers = ["plan", "how to", "approach", "steps"]
    priority = 7


class CritiqueSkill(Skill):
    """Skill for critique."""
    
    name = "critique"
    description = """
You are a critique expert. Evaluate:
- Is this the simplest solution?
- Does it solve the actual problem?
- What are the tradeoffs?
- What could go wrong?

Be honest but constructive.
"""
    triggers = ["evaluate", "assess", "critique", "opinion"]
    priority = 4


class GitHubSkill(Skill):
    """Skill for GitHub interaction."""
    
    name = "github"
    description = """
    You are a GitHub expert. You can:
    - Search for repositories
    - Create issues
    - Manage pull requests
    
    Use the GitHub API via available tools.
    """
    triggers = ["github", "pr", "issue", "repo", "repository"]
    priority = 9


class GitHubPRReviewSkill(Skill):
    """Skill for PR reviews."""
    
    name = "github-pr-review"
    description = """
    You are a GitHub PR review expert.
    - Provide inline comments and suggestions
    - Use appropriate priority labels
    """
    triggers = ["pr review", "review pr", "pull request review"]
    priority = 10


# Register all skills
_registry.register(CodeReviewSkill())
_registry.register(DebugSkill())
_registry.register(RefactorSkill())
_registry.register(TestSkill())
_registry.register(DocsSkill())
_registry.register(SecuritySkill())
_registry.register(PlanningSkill())
_registry.register(CritiqueSkill())
_registry.register(GitHubSkill())
_registry.register(GitHubPRReviewSkill())


# =============================================================================
# Skill Functions
# =============================================================================

def get_skill(name: str, **config) -> Skill:
    """Get a skill by name."""
    skill = _registry.get(name)
    if skill:
        return skill.__class__(**config)
    raise ValueError(f"Unknown skill: {name}")


def list_skills() -> list[str]:
    """List all available skills."""
    return _registry.list_all()


def find_skills(message: str) -> list[Skill]:
    """Find skills matching a message."""
    return _registry.find(message)


def register_skill(skill: Skill) -> None:
    """Register a custom skill."""
    _registry.register(skill)