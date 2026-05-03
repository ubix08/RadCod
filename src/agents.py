"""
RadCode Specialized Agents.

Implements Devin's specialized agent pattern:
- BackendAgent: API, database, server expertise
- FrontendAgent: UI, React, web expertise  
- TestAgent: Testing, QA expertise
- DevOpsAgent: Deployment, Docker, Cloud
- CodeReviewAgent: Code review expertise

Use:
    from src.agents import get_specialized_agent, AgentType
    
    agent = get_specialized_agent(AgentType.BACKEND)
    result = agent.run("Create a REST API")
"""

import os
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger("radcod.agents")


class AgentType(Enum):
    """Specialized agent types."""
    GENERAL = "general"      # Default - handles anything
    BACKEND = "backend"      # FastAPI, Django, Express, SQL
    FRONTEND = "frontend"   # React, Vue, HTML/CSS
    TEST = "test"           # Testing, QA, integration
    DEVOPS = "devops"       # Docker, Kubernetes, cloud
    CODE_REVIEW = "code_review"  # PR review, linting


# ============ AGENT PROMPTS ============

BACKEND_PROMPT = """
# Backend Agent - API & Server Specialist

You are an expert backend developer specializing in:
- FastAPI, Django, Express, Flask
- REST APIs, GraphQL, WebSockets
- PostgreSQL, MySQL, MongoDB
- Authentication, authorization, JWT
- Server optimization, caching

When asked to build backend:
1. Create proper project structure
2. Implement APIs with best practices
3. Add database models and migrations
4. Include error handling and validation
5. Write tests for core functionality
"""

FRONTEND_PROMPT = """
# Frontend Agent - UI Specialist

You are an expert frontend developer specializing in:
- React, Vue, Angular, Svelte
- Modern JavaScript/TypeScript
- CSS, Tailwind, styled-components
- UI components, responsive design
- State management (Redux, Zustand)

When asked to build frontend:
1. Create proper project structure
2. Use modern framework (prefer React)
3. Implement responsive components
4. Add proper styling and animations
5. Ensure accessibility
"""

TEST_PROMPT = """
# Test Agent - Quality Assurance

You are an expert QA engineer specializing in:
- Unit tests, integration tests, E2E
- pytest, Jest, Playwright
- Test-driven development (TDD)
- Mocking, fixtures
- Coverage analysis

When asked to write tests:
1. Follow TDD approach
2. Write meaningful test cases
3. Use proper fixtures and mocks
4. Aim for >80% coverage
5. Include edge cases
"""

DEVOPS_PROMPT = """
# DevOps Agent - Deployment Specialist

You are an expert DevOps engineer specializing in:
- Docker, Kubernetes
- AWS, GCP, Azure
- CI/CD pipelines
- Docker Compose
- Security best practices

When asked to deploy:
1. Create Dockerfile with proper config
2. Set up docker-compose
3. Configure environment variables
4. Add health checks
5. Document deployment steps
"""

CODE_REVIEW_PROMPT = """
# Code Review Agent - Review Specialist

You are an expert code reviewer specializing in:
- Code quality and best practices
- Security vulnerabilities
- Performance issues
- Code style consistency
- Pull request review

When asked to review code:
1. Check for bugs and issues
2. Verify security best practices
3. Look for performance problems
4. Ensure code style consistency
5. Provide constructive feedback
"""


# ============ AGENT CLASSES ============

class SpecializedAgent:
    """Base class for specialized agents."""
    
    def __init__(
        self,
        agent_type: AgentType,
        workspace: str = "./workspace",
        security_level: str = "medium",
        **kwargs
    ):
        self.agent_type = agent_type
        self.workspace = workspace
        self.security_level = security_level
        self._kwargs = kwargs
        self._coordinator = None
    
    def _get_coordinator(self):
        """Lazy load coordinator."""
        if self._coordinator is None:
            from src.coordinator import RadcodeCoordinator
            self._coordinator = RadcodeCoordinator(
                workspace=self.workspace,
                security_level=self.security_level,
                **self._kwargs
            )
        return self._coordinator
    
    def run(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Run task with specialized agent.
        
        Args:
            task: The task description
            
        Returns:
            Dict with results
        """
        logger.info(f"Running task with {self.agent_type.value} agent")
        
        # Get the coordinator
        coord = self._get_coordinator()
        
        # Run with the agent
        result = coord.run(task, **kwargs)
        
        return result
    
    @property
    def conversation(self):
        """Get the conversation for streaming."""
        return self._get_coordinator().conversation


class BackendAgent(SpecializedAgent):
    """Backend-specialized agent."""
    
    def __init__(self, **kwargs):
        super().__init__(AgentType.BACKEND, **kwargs)
        self._system_prompt = BACKEND_PROMPT


class FrontendAgent(SpecializedAgent):
    """Frontend-specialized agent."""
    
    def __init__(self, **kwargs):
        super().__init__(AgentType.FRONTEND, **kwargs)
        self._system_prompt = FRONTEND_PROMPT


class TestAgent(SpecializedAgent):
    """Test-specialized agent."""
    
    def __init__(self, **kwargs):
        super().__init__(AgentType.TEST, **kwargs)
        self._system_prompt = TEST_PROMPT


class DevOpsAgent(SpecializedAgent):
    """DevOps-specialized agent."""
    
    def __init__(self, **kwargs):
        super().__init__(AgentType.DEVOPS, **kwargs)
        self._system_prompt = DEVOPS_PROMPT


class CodeReviewAgent(SpecializedAgent):
    """Code review specialized agent."""
    
    def __init__(self, **kwargs):
        super().__init__(AgentType.CODE_REVIEW, **kwargs)
        self._system_prompt = CODE_REVIEW_PROMPT


# ============ FACTORY FUNCTION ============

def get_specialized_agent(
    agent_type: AgentType,
    workspace: str = "./workspace",
    security_level: str = "medium",
    **kwargs
) -> SpecializedAgent:
    """
    Factory function to get a specialized agent.
    
    Args:
        agent_type: Type of specialized agent
        workspace: Working directory
        security_level: Security level
        **kwargs: Additional arguments
        
    Returns:
        Specialized agent instance
    """
    agents = {
        AgentType.BACKEND: BackendAgent,
        AgentType.FRONTEND: FrontendAgent,
        AgentType.TEST: TestAgent,
        AgentType.DEVOPS: DevOpsAgent,
        AgentType.CODE_REVIEW: CodeReviewAgent,
        AgentType.GENERAL: SpecializedAgent,
    }
    
    agent_class = agents.get(agent_type, SpecializedAgent)
    return agent_class(
        agent_type=agent_type,
        workspace=workspace,
        security_level=security_level,
        **kwargs
    )


def detect_agent_type(task: str) -> AgentType:
    """
    Detect agent type from task description.
    
    Args:
        task: Task description
        
    Returns:
        Detected agent type
    """
    task_lower = task.lower()
    
    # Backend keywords
    if any(kw in task_lower for kw in [
        "api", "backend", "fastapi", "django", "express", 
        "server", "database", "sql", "postgresql", "mysql",
        "mongodb", "rest", "graphql", "auth"
    ]):
        return AgentType.BACKEND
    
    # Frontend keywords
    if any(kw in task_lower for kw in [
        "frontend", "ui", "react", "vue", "angular",
        "web", "component", "css", "html", "javascript",
        "dashboard", "page", "button", "form"
    ]):
        return AgentType.FRONTEND
    
    # Test keywords
    if any(kw in task_lower for kw in [
        "test", "testing", "spec", "qa", "e2e",
        "integration", "unit test", "jest", "pytest"
    ]):
        return AgentType.TEST
    
    # DevOps keywords
    if any(kw in task_lower for kw in [
        "deploy", "docker", "kubernetes", "k8s",
        "cloud", "aws", "gcp", "azure", "ci/cd",
        "pipeline", "container"
    ]):
        return AgentType.DEVOPS
    
    # Code review keywords
    if any(kw in task_lower for kw in [
        "review", "pr", "merge", "lint", "fix",
        "security", "vulnerability"
    ]):
        return AgentType.CODE_REVIEW
    
    # Default to general
    return AgentType.GENERAL


# ============ INTEGRATION WITH ORCHESTRATOR ============

def get_agent_for_subtask(subtask_name: str) -> AgentType:
    """
    Map subtask name to agent type for orchestrator.
    
    Used by orchestrator to assign correct agent type to each subtask.
    
    Args:
        subtask_name: Name of subtask
        
    Returns:
        Agent type to use
    """
    name_lower = subtask_name.lower()
    
    if "backend" in name_lower or "api" in name_lower:
        return AgentType.BACKEND
    if "frontend" in name_lower or "ui" in name_lower:
        return AgentType.FRONTEND
    if "test" in name_lower or "spec" in name_lower:
        return AgentType.TEST
    if "deploy" in name_lower or "docker" in name_lower:
        return AgentType.DEVOPS
    if "review" in name_lower:
        return AgentType.CODE_REVIEW
    
    return AgentType.GENERAL


# ============ CLI ============

def main():
    """CLI for specialized agents."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python -m src.agents <agent_type> <task>")
        print("Agent types: backend, frontend, test, devops, code_review, general")
        print("Example: python -m src.agents backend 'Create a user API'")
        sys.exit(1)
    
    agent_type_str = sys.argv[1].lower()
    task = " ".join(sys.argv[2:])
    
    try:
        agent_type = AgentType(agent_type_str)
    except ValueError:
        print(f"Unknown agent type: {agent_type_str}")
        sys.exit(1)
    
    agent = get_specialized_agent(agent_type)
    result = agent.run(task)
    
    print(f"\n=== Result ===")
    print(f"Agent: {agent_type.value}")
    print(f"Status: {result.get('status', 'unknown')}")


if __name__ == "__main__":
    main()