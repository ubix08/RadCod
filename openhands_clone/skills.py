"""
OpenHands-Clone Skills - Phase 1
=================================
Skill system for the coding agent.
"""

from openhands.sdk.skill import Skill as SDKSkill

# =============================================================================
# Skill Base Class
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

# Global registry (using standard dictionary)
_registry = {}

def register_skill(skill: Skill) -> None:
    """Register a skill."""
    _registry[skill.name] = skill

def get_skill(name: str, **config) -> Skill:
    """Get a skill by name."""
    skill = _registry.get(name)
    if skill:
        return skill.__class__(**config)
    raise ValueError(f"Unknown skill: {name}")

def list_skills() -> list[str]:
    """List all available skills."""
    return list(_registry.keys())

def find_skills(message: str) -> list[Skill]:
    """Find skills matching a message."""
    matches = [s for s in _registry.values() if s.should_activate(message)]
    return sorted(matches, key=lambda s: s.priority, reverse=True)

# =============================================================================
# Built-in Skills (Retaining original definitions)
# =============================================================================

class CodeReviewSkill(Skill):
    """Skill for code review."""
    name = "code-review"
    description = "You are a code review expert..."
    triggers = ["review", "code review"]
    priority = 10

class DebugSkill(Skill):
    """Skill for debugging."""
    name = "debug"
    description = "You are a debugging expert..."
    triggers = ["debug", "fix"]
    priority = 10

class RefactorSkill(Skill):
    """Skill for code refactoring."""
    name = "refactor"
    description = "You are a refactoring expert..."
    triggers = ["refactor", "simplify"]
    priority = 5

class TestSkill(Skill):
    """Skill for testing."""
    name = "test"
    description = "You are a testing expert..."
    triggers = ["test", "verify"]
    priority = 5

class DocsSkill(Skill):
    """Skill for documentation."""
    name = "docs"
    description = "You are a documentation expert..."
    triggers = ["document", "docs"]
    priority = 3

class SecuritySkill(Skill):
    """Skill for security."""
    name = "security"
    description = "You are a security expert..."
    triggers = ["security", "secure"]
    priority = 8

class PlanningSkill(Skill):
    """Skill for planning."""
    name = "planning"
    description = "You are a planning expert..."
    triggers = ["plan", "approach"]
    priority = 7

class CritiqueSkill(Skill):
    """Skill for critique."""
    name = "critique"
    description = "You are a critique expert..."
    triggers = ["evaluate", "critique"]
    priority = 4

class GitHubSkill(Skill):
    """Skill for GitHub interaction."""
    name = "github"
    description = "GitHub expert."
    triggers = ["github", "pr"]
    priority = 9

class GitHubPRReviewSkill(Skill):
    """Skill for PR reviews."""
    name = "github-pr-review"
    description = "PR review expert."
    triggers = ["pr review"]
    priority = 10

# Register all skills
register_skill(CodeReviewSkill())
register_skill(DebugSkill())
register_skill(RefactorSkill())
register_skill(TestSkill())
register_skill(DocsSkill())
register_skill(SecuritySkill())
register_skill(PlanningSkill())
register_skill(CritiqueSkill())
register_skill(GitHubSkill())
register_skill(GitHubPRReviewSkill())
