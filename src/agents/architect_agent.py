"""
Architect/Planner Agent - Designs complex project architecture.

Creates MasterProjectSpec with detailed planning for complex projects.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.orchestrator.skills import load_skill
from src.orchestrator.master_spec import (
    MasterProjectSpec, ProjectConversation,
    ProjectPhase, ComplexityLevel, ProjectPriority,
    ProjectMilestone, Integration, Team,
    ProjectConversation
)

logger = logging.getLogger("radcod.architect")


@dataclass
class ArchitectOutput:
    """Output from the architect agent."""
    master_spec: MasterProjectSpec
    conversation: ProjectConversation
    recommendation: str  # Should proceed / Need more info


class ArchitectAgent:
    """
    Architect Agent - Plans complex project architecture.
    
    Workflow:
    1. Start conversation to gather requirements
    2. Use DeepSearch for domain research (if needed)
    3. Create detailed MasterProjectSpec
    4. Plan milestones and phases
    5. Output plan for execution
    """
    
    def __init__(self):
        self.skill = load_skill("architect")
        self._conversation = None
        logger.info("Architect Agent initialized.")
    
    def start_conversation(self, project_name: str = "") -> ProjectConversation:
        """Start a clarification conversation."""
        self._conversation = ProjectConversation(project_name)
        return self._conversation
    
    def _generate_clarification_questions(
        self, 
        user_request: str,
        entity_count: int = 0
    ) -> List[str]:
        """Generate relevant clarification questions based on project."""
        questions = []
        
        # Generic questions for all projects
        questions.append("Who are the primary users of this system?")
        questions.append("What is the expected user volume?")
        
        # Entity-based questions
        if entity_count > 3:
            questions.append("How do these entities relate to each other?")
            questions.append("What are the main workflows between entities?")
        
        # Inventory-specific questions
        if "inventory" in user_request.lower() or "stock" in user_request.lower():
            questions.extend([
                "Do you track variants (size, color, etc.)?",
                "What is your reorder point logic?",
                "Do you need warehouse/location tracking?",
                "What integrations are needed? (accounting, POS, ecommerce)"
            ])
        
        # E-commerce questions
        if "shop" in user_request.lower() or "store" in user_request.lower():
            questions.extend([
                "What payment processors needed?",
                "Do you need shipping integration?",
                "Tax calculation requirements?"
            ])
        
        return questions[:5]  # Return max 5 questions
    
    def generate_plan(
        self,
        user_request: str,
        initial_entities: List[str] = None,
        research_data: Dict[str, Any] = None
    ) -> ArchitectOutput:
        """
        Generate a comprehensive master project plan.
        
        Args:
            user_request: Initial user request
            initial_entities: List of entities from business analysis
            research_data: Optional research from DeepSearch
            
        Returns:
            ArchitectOutput with MasterProjectSpec
        """
        logger.info(f"Generating plan for: {user_request}")
        
        project_name = self._extract_project_name(user_request)
        
        # Start conversation
        conversation = self.start_conversation(project_name)
        conversation.add_user_message(user_request)
        
        # Determine complexity
        entity_count = len(initial_entities) if initial_entities else 1
        if entity_count <= 2:
            complexity = ComplexityLevel.SIMPLE
        elif entity_count <= 5:
            complexity = ComplexityLevel.MODERATE
        elif entity_count <= 15:
            complexity = ComplexityLevel.COMPLEX
        else:
            complexity = ComplexityLevel.ENTERPRISE
        
        # Generate questions
        questions = self._generate_clarification_questions(
            user_request, 
            entity_count
        )
        
        # Need more info if complex
        if complexity.value in ("complex", "enterprise"):
            conversation.add_assistant_message(
                f"This appears to be a {complexity.value} project. I have some questions:",
                questions
            )
            
            # Create draft spec
            master_spec = MasterProjectSpec(
                project_name=project_name,
                business_name=project_name,
                business_description=user_request,
                complexity=complexity,
                user_requirements=[user_request],
                clarification_questions=questions,
                clear_objective="",
                status="draft"
            )
            
            return ArchitectOutput(
                master_spec=master_spec,
                conversation=conversation,
                recommendation="Need more info"
            )
        
        # For simpler projects, create full plan
        return self._create_full_plan(
            project_name, 
            user_request,
            initial_entities,
            research_data
        )
    
    def _extract_project_name(self, request: str) -> str:
        """Extract project name from request."""
        # Simple extraction - would use LLM in production
        words = request.split()
        for word in ["system", "app", "application", "for"]:
            if word in words:
                idx = words.index(word)
                if idx + 1 < len(words):
                    return " ".join(words[idx+1:]).title()
        
        return words[0].title() if words else "Project"
    
    def _create_full_plan(
        self,
        project_name: str,
        user_request: str,
        initial_entities: List[str] = None,
        research_data: Dict[str, Any] = None
    ) -> ArchitectOutput:
        """Create full project plan."""
        
        conversation = self.start_conversation(project_name)
        conversation.add_user_message(user_request)
        
        # Build MasterProjectSpec
        master_spec = MasterProjectSpec(
            project_name=project_name,
            business_name=project_name,
            business_description=user_request,
            complexity=ComplexityLevel.MODERATE,
            priority=ProjectPriority.MEDIUM,
            user_requirements=[user_request],
            clear_objective=f"Build a {project_name} system",
            status="planned"
        )
        
        # Tech stack suggestions
        master_spec.tech_stack = {
            "Backend": "FastAPI",
            "Database": "PostgreSQL",
            "Frontend": "React",
            "Hosting": "Cloud (AWS/GCP)"
        }
        
        # Add milestones based on complexity
        self._plan_milestones(master_spec)
        
        # Add teams
        self._plan_teams(master_spec)
        
        conversation.add_assistant_message(
            f"Plan created for {project_name}",
            []
        )
        
        return ArchitectOutput(
            master_spec=master_spec,
            conversation=conversation,
            recommendation="Ready for implementation"
        )
    
    def _plan_milestones(self, spec: MasterProjectSpec):
        """Plan project milestones."""
        # Phase 1: Foundation
        spec.add_milestone(
            name="Project Setup",
            description="Initialize project, set up infrastructure",
            phase=ProjectPhase.FOUNDATION
        )
        
        # Phase 2: Core Data
        for entity in spec.domain_spec.entities if spec.domain_spec else []:
            name = f"{entity.name} Management"
            spec.add_milestone(
                name=name,
                description=f"CRUD for {entity.name}",
                phase=ProjectPhase.IMPLEMENTATION
            )
        
        # Phase 3: API
        spec.add_milestone(
            name="REST API",
            description="Expose all endpoints",
            phase=ProjectPhase.IMPLEMENTATION
        )
        
        # Phase 4: UI
        spec.add_milestone(
            name="User Interface",
            description="Build frontend",
            phase=ProjectPhase.IMPLEMENTATION
        )
        
        # Phase 5: Integration
        if spec.integrations:
            spec.add_milestone(
                name="Integrations",
                description="Connect external systems",
                phase=ProjectPhase.INTEGRATION
            )
        
        # Phase 6: Testing
        spec.add_milestone(
            name="QA Testing",
            description="Test all features",
            phase=ProjectPhase.TESTING
        )
        
        # Phase 7: Deploy
        spec.add_milestone(
            name="Production Launch",
            description="Deploy to production",
            phase=ProjectPhase.DEPLOYMENT
        )
    
    def _plan_teams(self, spec: MasterProjectSpec):
        """Plan project teams."""
        spec.teams.append(Team(
            name="Development",
            role="Backend/Frontend",
            responsibilities=["Build features", "Code review"],
            size=2
        ))
        
        spec.teams.append(Team(
            name="QA",
            role="Testing",
            responsibilities=["Test plans", "Bug reporting"],
            size=1
        ))
    
    def refine_plan(
        self,
        master_spec: MasterProjectSpec,
        user_answers: Dict[str, str]
    ) -> MasterProjectSpec:
        """Refine plan based on user answers."""
        
        # Update clear objective
        if user_answers:
            answers = "; ".join(
                f"{k}: {v}" for k, v in user_answers.items()
            )
            master_spec.clear_objective = answers
        
        # Re-plan milestones based on answers
        master_spec.milestones = []
        self._plan_milestones(master_spec)
        
        # Update status
        master_spec.status = "approved"
        
        logger.info(f"Plan refined: {master_spec.project_name}")
        
        return master_spec


def create_architect_agent() -> ArchitectAgent:
    """Factory function."""
    return ArchitectAgent()