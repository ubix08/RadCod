"""
Master Project Specification - For Complex Multi-Entity Projects.

Handles complex business applications that require:
- Multiple phases
- Multiple teams/departments
- Integration requirements
- Detailed planning
- Resource allocation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

from src.orchestrator.domain_spec.models import DomainSpec


class ProjectPhase(str, Enum):
    """Phases of a complex project."""
    DISCOVERY = "discovery"           # Requirements gathering
    PLANNING = "planning"            # Architecture design
    FOUNDATION = "foundation"        # Core infrastructure
    IMPLEMENTATION = "implementation" # Feature development
    INTEGRATION = "integration"      # System integration
    TESTING = "testing"             # QA and testing
    DEPLOYMENT = "deployment"       # Production release
    MAINTENANCE = "maintenance"    # Ongoing support


class ProjectPriority(str, Enum):
    """Project priority levels."""
    CRITICAL = "critical"    # Business critical
    HIGH = "high"          # Important
    MEDIUM = "medium"      # Standard
    LOW = "low"           # Nice to have


class ComplexityLevel(str, Enum):
    """Project complexity levels."""
    SIMPLE = "simple"          # Single entity, basic CRUD
    MODERATE = "moderate"    # 2-5 entities
    COMPLEX = "complex"     # 5-15 entities, integrations
    ENTERPRISE = "enterprise" # 15+ entities, multiple systems


@dataclass
class ProjectMilestone:
    """A major project milestone."""
    name: str
    description: str
    phase: ProjectPhase
    deliverables: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_hours: float = 0.0
    completed_at: Optional[datetime] = None
    
    @property
    def is_complete(self) -> bool:
        return self.completed_at is not None


@dataclass
class Integration:
    """Integration with external systems."""
    name: str
    system_type: str  # payment, crm, accounting, etc.
    api_endpoint: str = ""
    description: str = ""
    required: bool = False


@dataclass
class Team:
    """Project team or department."""
    name: str
    role: str  # developers, qa, operations
    responsibilities: List[str] = field(default_factory=list)
    size: int = 1


@dataclass
class MasterProjectSpec:
    """
    Master specification for complex projects.
    
    Generated through conversation/clarification with user,
    then planned by architect agent.
    """
    project_name: str
    business_name: str
    business_description: str
    
    # Project classification
    complexity: ComplexityLevel = ComplexityLevel.MODERATE
    priority: ProjectPriority = ProjectPriority.MEDIUM
    
    # Requirements
    user_requirements: List[str] = field(default_factory=list)
    clarification_questions: List[str] = field(default_factory=list)
    clear_objective: str = ""
    
    # Domain (from BusinessAnalyst)
    domain_spec: Optional[DomainSpec] = None
    
    # Architecture
    tech_stack: Dict[str, str] = field(default_factory=dict)
    architecture_diagram: str = ""
    
    # Phases and milestones
    phases: List[ProjectPhase] = field(default_factory=list)
    milestones: List[ProjectMilestone] = field(default_factory=list)
    
    # Integrations
    integrations: List[Integration] = field(default_factory=list)
    
    # Teams
    teams: List[Team] = field(default_factory=list)
    
    # Resource estimation
    estimated_total_hours: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    status: str = "draft"  # draft, planned, approved, in_progress, complete
    
    def to_markdown(self) -> str:
        """Convert to Markdown for planning."""
        md = f"""# Master Project Specification: {self.project_name}

**Version:** {self.version} | **Status:** {self.status}
**Complexity:** {self.complexity.value} | **Priority:** {self.priority.value}

## Business Overview
- **Business Name:** {self.business_name}
- **Description:** {self.business_description}

## Clear Objective
{self.clear_objective}

## Requirements ({len(self.user_requirements)} items)
"""
        for req in self.user_requirements:
            md += f"- {req}\n"
        
        if self.clarification_questions:
            md += f"\n### Clarification Needed\n"
            for q in self.clarification_questions:
                md += f"- {q}\n"
        
        md += "\n## Architecture\n"
        for tech, choice in self.tech_stack.items():
            md += f"- **{tech}:** {choice}\n"
        
        if self.integrations:
            md += "\n## Integrations\n"
            for int_ in self.integrations:
                req = "[Required]" if int_.required else "[Optional]"
                md += f"- {int_.name} ({int_.system_type}) {req}\n"
        
        if self.milestones:
            md += "\n## Implementation Plan\n"
            for ms in self.milestones:
                md += f"### {ms.name}\n"
                md += f"- Phase: {ms.phase.value}\n"
                md += f"- Description: {ms.description}\n"
                if ms.estimated_hours:
                    md += f"- Estimate: {ms.estimated_hours}h\n"
        
        if self.estimated_total_hours:
            md += f"\n## Total Estimate\n**{self.estimated_total_hours} hours**\n"
        
        return md
    
    def add_milestone(self, name: str, description: str, phase: ProjectPhase):
        """Add a project milestone."""
        milestone = ProjectMilestone(
            name=name,
            description=description,
            phase=phase
        )
        self.milestones.append(milestone)
        return milestone
    
    def add_integration(self, name: str, system_type: str, required: bool = False):
        """Add an integration requirement."""
        integration = Integration(
            name=name,
            system_type=system_type,
            required=required
        )
        self.integrations.append(integration)
        return integration
    
    def get_required_integrations(self) -> List[Integration]:
        """Get required integrations only."""
        return [i for i in self.integrations if i.required]
    
    def get_phase_milestones(self, phase: ProjectPhase) -> List[ProjectMilestone]:
        """Get milestones for a specific phase."""
        return [m for m in self.milestones if m.phase == phase]


@dataclass
class ConversationTurn:
    """A single turn in the clarification conversation."""
    role: str = ""
    message: str = ""
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class ProjectConversation:
    """Conversation manager for project clarification."""
    
    def __init__(self, project_name: str = ""):
        self.project_name = project_name
        self.turns: List[ConversationTurn] = []
        self.pending_questions: List[str] = []
        self.gathered_requirements: List[str] = []
        self.status: str = "gathering"  # gathering, clarifying, complete
    
    def add_user_message(self, message: str):
        """Add user's message."""
        turn = ConversationTurn(role="user", message=message)
        self.turns.append(turn)
        
        # Extract potential requirements
        if message:
            self.gathered_requirements.append(message)
    
    def add_assistant_message(self, message: str, questions: List[str] = None):
        """Add assistant's message with follow-up questions."""
        turn = ConversationTurn(
            role="assistant", 
            message=message,
            metadata={"questions": questions or []}
        )
        self.turns.append(turn)
        
        if questions:
            self.pending_questions.extend(questions)
    
    def add_question(self, question: str):
        """Add a clarification question."""
        if question not in self.pending_questions:
            self.pending_questions.append(question)
    
    def answer_question(self, question: str, answer: str):
        """Answer a pending question."""
        if question in self.pending_questions:
            self.pending_questions.remove(question)
            
            # Record the answer
            turn = ConversationTurn(
                role="user",
                message=f"Q: {question}\nA: {answer}"
            )
            self.turns.append(turn)
            
            # Add to requirements
            self.gathered_requirements.append(f"{question}: {answer}")
    
    def is_complete(self) -> bool:
        """Check if clarification is complete."""
        return len(self.pending_questions) == 0 and len(self.gathered_requirements) >= 3
    
    def get_summary(self) -> str:
        """Get conversation summary."""
        return f"""Requirements gathered ({len(self.gathered_requirements)}):
{chr(10).join(f"- {r}" for r in self.gathered_requirements)}

Pending questions: {len(self.pending_questions)}
"""