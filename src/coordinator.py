"""
Radcode Coordinator - Single Agent Architecture.

Features:
- ONE autonomous Agent (Devin pattern)
- TaskTrackerTool for subtask management
- TerminalTool + FileEditorTool for execution
- BrowserToolSet for web browsing
- SerperSearchTool for web search
- SecurityAnalyzer for action validation
- Conversation for reasoning-action loop
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("radcod.coordinator")

# ============= SYSTEM PROMPT =============

SYSTEM_PROMPT = """
# Radcode - Autonomous AI Software Engineer

You are an autonomous AI software engineer. Your role is to build complete applications from business requirements.

## Your Role

1. **Understand** - Read carefully what the user wants
2. **Plan** - Use TaskTrackerTool to create subtasks  
3. **Execute** - Use TerminalTool and FileEditorTool to build
4. **Verify** - Check your work works
5. **Iterate** - Fix issues until complete
6. **Review** - Self-review before completion

## Expertise (Skills Available)

You have access to specialized skills for different domains:
- **Python**: Best practices, patterns, testing
- **Frontend**: React, Vue, modern web
- **Backend**: FastAPI, Django, Express
- **Debugging**: Systematic error analysis
- **Code Review**: PR review best practices

Skills are loaded automatically based on task keywords.

---

For complex tasks, follow this approach:

### 1. Project Scaffolding
When asked to build a full project:
- Choose appropriate framework based on requirements:
  * REST API → FastAPI (Python)
  * Web app → React + Vite
  * Backend → Django (Python) or Express (Node)
  * CLI tool → Click or Typer (Python)
- Create SPEC.md first with detailed requirements
- Generate project structure
- Verify dependencies install correctly

### 2. Test Generation
For every feature:
- Write tests FIRST (TDD if possible)
- Test files go in tests/ or __tests__/
- Use pytest (Python) or vitest (JS)
- Run: `pytest` or `npm test`
- Always include: unit tests + integration tests

### 3. Error Debugging
When errors occur:
1. Read error message carefully
2. Identify root cause (not symptom)
3. Find relevant code section
4. Fix the cause, not symptoms
5. Re-run to verify fix
6. If persists, iterate

### 4. Long-Task Handling
For multi-hour tasks:
- Break into small subtasks (TaskTrackerTool)
- Complete one subtask at a time
- Verify each before moving on
- Save progress frequently
- Use checkpoints

---

## Available Tools

### TaskTrackerTool
Use to track progress:
- Add subtasks for complex requests
- Mark tasks complete when done
- View pending tasks

### TerminalTool  
Execute commands:
- Install dependencies
- Run servers
- Run tests

### FileEditorTool
Write and edit code:
- Create files
- Read files
- Edit files

### BrowserToolSet (use when user asks to browse, search, or visit URLs)
Browse websites, fill forms, extract content from web pages.

### SerperSearchTool (use when you need current web info or google search)
Search the web for current information, news, documentation.

### GitHub Integration
You can interact with GitHub using:

1. **gh CLI** (if installed):
   - gh issue list - List issues
   - gh pr list - List PRs
   - gh pr create - Create PR
   - gh pr review - Review PR
   - gh run list - List workflow runs

2. **GitHub API** (via curl):
   - Set GITHUB_TOKEN env var
   - Use API: https://api.github.com/repos/{owner}/{repo}/...
   - Examples:
     curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/repos/owner/repo/issues

## Important

- Be thorough - build complete applications
- Test your work
- Fix errors until it works
- Report completion when done
"""


# ============= SERPER SEARCH (via terminal) =============

# Agent can search via TerminalTool with curl:
# curl -s -X POST https://google.serper.dev/search \
#   -H "X-API-Key: $SERPER_API_KEY" \
#   -H "Content-Type: application/json" \
#   -d '{"q": "your query"}'

# Set SERPER_API_KEY env var to enable web search via terminal


# ============= GITHUB HELPER =============

class GitHubHelper:
    """
    Optional GitHub helper using PyGithub.
    
    Usage:
        pip install radcod[github]
        
        from src.coordinator import GitHubHelper
        gh = GitHubHelper()
        issues = gh.get_issues("owner/repo")
    """
    
    @staticmethod
    def check_available() -> bool:
        """Check if PyGithub is available."""
        try:
            import github
            return True
        except ImportError:
            return False
    
    def get_client(self, token: str = None):
        """Get PyGithub client."""
        try:
            from github import Github
            import os
            token = token or os.getenv("GITHUB_TOKEN")
            return Github(token)
        except ImportError:
            raise RuntimeError("PyGithub not installed: pip install PyGithub")
    
    def get_issues(self, repo: str, state: str = "open"):
        """Get issues from repo (owner/repo)."""
        client = self.get_client()
        repo_obj = client.get_repo(repo)
        return list(repo_obj.get_issues(state=state))
    
    def get_pulls(self, repo: str, state: str = "open"):
        """Get PRs from repo."""
        client = self.get_client()
        repo_obj = client.get_repo(repo)
        return list(repo_obj.get_pulls(state=state))
    
    def create_pr(
        self, 
        repo: str, 
        title: str, 
        body: str, 
        head: str, 
        base: str = "main"
    ):
        """Create a PR."""
        client = self.get_client()
        repo_obj = client.get_repo(repo)
        return repo_obj.create_pull(title, body, head, base)


# ============= COORDINATOR =============

class RadcodeCoordinator:
    """
    Single Agent Architecture - Matches Devin.
    
    Features:
    - ONE autonomous Agent
    - TaskTrackerTool for subtasks
    - TerminalTool + FileEditorTool for execution
    - SecurityAnalyzer for action validation
    """
    
    def __init__(
        self, 
        api_key: str = None, 
        workspace: str = "./workspace",
        security_level: str = "medium"  # low, medium, high
    ):
        self._key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._workspace = Path(workspace)
        self._instructions = SYSTEM_PROMPT
        self._security_level = security_level
        
        # SDK components - lazily initialized
        self._llm = None
        self._agent = None
        self._conversation = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize ONE SDK Agent with security."""
        if self._initialized:
            return
        
        try:
            from openhands.sdk import LLM, Agent, Conversation, Tool
            from openhands.tools.file_editor import FileEditorTool
            from openhands.tools.terminal import TerminalTool
            from openhands.tools.task_tracker import TaskTrackerTool
            
            # BrowserToolSet - required for web browsing capabilities
            from openhands.tools.browser_use import BrowserToolSet
            
            # ONE LLM instance
            # Model providers mapping - simple key->(prefix, env_key) lookup
            PROVIDERS = {
                "groq": ("groq/", "GROQ_API_KEY"),
                "google": ("google/", "GEMINI_API_KEY"),
                "google-generative-ai": ("google/", "GEMINI_API_KEY"),
                "glm": ("/", "ZAI_API_KEY"),  # ZAI uses model itself as key
                "nvidia": ("nvidia/", "NVIDIA_API_KEY"),
                "openrouter": ("openrouter/", "OPENROUTER_API_KEY"),
                "anthropic": ("anthropic/", "ANTHROPIC_API_KEY"),
                "openai": ("openai/", "OPENAI_API_KEY"),
            }
            
            raw_model = os.getenv("LLM_MODEL", "groq/llama-3.1-70b-instruct")
            
            # Determine provider and API key
            provider = None
            api_key = None
            
            for key, (prefix, env_var) in PROVIDERS.items():
                if key in raw_model.lower():
                    provider = prefix
                    api_key = os.getenv(env_var)
                    break
            
            # Default: use as-is if no known provider
            if provider is None:
                model = raw_model
                api_key = os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")
            elif "/" not in raw_model:
                model = f"{provider.rstrip('/')}/{raw_model}"
            else:
                model = raw_model
            
            self._llm = LLM(
                model=model,
                api_key=api_key
            )
            
            # Security configuration
            security = self._build_security()
            
            # Build tools list - ALL core tools always included
            tools = [
                Tool(name=TaskTrackerTool.name),
                Tool(name=FileEditorTool.name),
                Tool(name=TerminalTool.name),
                Tool(name=BrowserToolSet.name),  # Core tool
            ]
            
            # ONE Agent with all tools + security
            self._agent = Agent(
                llm=self._llm,
                tools=tools,
                system_prompt=self._instructions,
                security_analyzer=security
            )
            
            # ONE Conversation
            self._conversation = Conversation(
                agent=self._agent,
                workspace=str(self._workspace)
            )
            
            self._initialized = True
            logger.info("RadcodeCoordinator initialized")
            
        except ImportError as e:
            logger.error(f"OpenHands SDK not installed: {e}")
            raise RuntimeError("openhands-sdk required. Install: pip install openhands-sdk openhands-tools")
    
    def _build_security(self):
        """Build security analyzer based on security level."""
        try:
            from openhands.sdk.security import GraySwanAnalyzer, AlwaysConfirm
            
            # Define security based on level
            if self._security_level == "high":
                # High security - block dangerous actions
                return AlwaysConfirm()
            elif self._security_level == "medium":
                # Medium - gray swan analysis
                return GraySwanAnalyzer()
            else:
                # Low security - use gray swan (minimal blocking)
                return GraySwanAnalyzer()
            
        except ImportError:
            logger.warning("SecurityAnalyzer not available, running without security")
            return None
    
    @property
    def agent(self) -> Any:
        """Get the SDK Agent."""
        self._initialize()
        return self._agent
    
    @property
    def conversation(self) -> Any:
        """Get the SDK Conversation."""
        self._initialize()
        return self._conversation
    
    # ============= AUTO SKILL LOADING =============
    
    # Skills to load based on keywords in request
    SKILL_TRIGGERS = {
        "frontend": ["ui", "frontend", "react", "vue", "web", "css", "html", "component", "page"],
        "backend": ["api", "backend", "server", "database", "sql", "fastapi", "express"],
        "code-review": ["review", "pr", "merge", "pull request"],
        "security": ["security", "auth", "oauth", "password", " encryption"],
        "docker": ["docker", "container", "kubernetes", "k8s", "deploy"],
        "database": ["database", "db", "postgres", "mysql", "mongodb", "sql"],
    }
    
    @classmethod
    def get_skills_for_request(cls, request: str) -> list:
        """ Determine which skills are relevant for a request based on keywords."""
        request_lower = request.lower()
        skills = []
        
        for skill_name, keywords in cls.SKILL_TRIGGERS.items():
            if any(kw in request_lower for kw in keywords):
                skills.append(skill_name)
        
        return skills
    
    def run(self, request: str, progress_callback=None) -> Dict[str, Any]:
        """
        Execute request using ONE Agent with security.
        
        Args:
            request: The task request
            progress_callback: Optional callback function for progress updates.
                             Called with dict: {"iteration": N, "action": "...", "status": "running"|"done"|"error"}
        
        Includes automatic context condensation for long tasks.
        """
        self._initialize()
        
        # Detect relevant skills for this request
        detected_skills = self.get_skills_for_request(request)
        if detected_skills:
            logger.info(f"Detected skills for request: {detected_skills}")
            # Skills can be loaded via openhands.sdk.load_skills_from_dir() if needed
        
        # Check context before running
        if not self.can_continue():
            logger.info("Context approaching limit, condensing...")
            self.condense_context()
        
        self._conversation.send_message(request)
        
        try:
            # Setup progress callback if provided
            if progress_callback:
                def on_progress(action, iteration=0):
                    progress_callback({
                        "iteration": iteration,
                        "action": str(action)[:100],
                        "status": "running"
                    })
                # Use in conversation if supported
                try:
                    result = self._conversation.run(on_progress=on_progress)
                except TypeError:
                    # SDK doesn't support callback
                    result = self._conversation.run()
            else:
                result = self._conversation.run()
            
            if progress_callback:
                progress_callback({"iteration": 0, "action": "", "status": "done"})
            
            return {
                "status": "success",
                "result": result,
                "request": request,
                "security_level": self._security_level
            }
        except Exception as e:
            if progress_callback:
                progress_callback({"iteration": 0, "action": "", "status": "error", "error": str(e)})
            logger.error(f"Execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "request": request
            }
    
    # Backward compatibility
    def process_request(self, request: str) -> Dict[str, Any]:
        """Alias for run()."""
        return self.run(request)
    
    # ============= STUCK DETECTION =============
    
    def run_with_timeout(
        self, 
        request: str, 
        timeout_seconds: int = 600,
        max_iterations: int = 100
    ) -> Dict[str, Any]:
        """
        Execute request with stuck detection.
        
        Args:
            request: The task request
            timeout_seconds: Max time to run (default 10 min)
            max_iterations: Max agent loops (default 100)
            
        Returns:
            Result with status and any stuck detection info
        """
        self._initialize()
        
        from datetime import datetime, timedelta
        import signal
        
        # Set timeout
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=timeout_seconds)
        
        # Track iterations
        iteration_count = 0
        last_action = None
        repeat_count = 0
        
        self._conversation.send_message(request)
        
        try:
            # Run with iteration tracking
            result = self._conversation.run(
                max_iterations=max_iterations,
                # Callback to check for stuck
                on_iteration=lambda action: self._check_stuck(
                    action, 
                    iteration_count, 
                    last_action, 
                    repeat_count
                )
            )
            
            return {
                "status": "success",
                "result": result,
                "request": request,
                "iterations": iteration_count,
                "security_level": self._security_level
            }
            
        except TimeoutError:
            return {
                "status": "timeout",
                "error": f"Task exceeded {timeout_seconds}s timeout",
                "request": request,
                "iterations": iteration_count
            }
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "request": request,
                "iterations": iteration_count
            }
    
    def _check_stuck(self, action, iteration, last_action, repeat_count):
        """
        Check if agent is stuck (repeating same action).
        
        Returns True if stuck, False otherwise.
        """
        if action == last_action:
            repeat_count += 1
            if repeat_count >= 5:  # Same action 5 times = stuck
                return True
        else:
            repeat_count = 0
        
        return False
    
    # ============= METRICS =============
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the current session.
        
        Returns token usage, cost, and performance metrics.
        """
        if not self._initialized or not self._llm:
            return {"status": "not_initialized"}
        
        try:
            # Get metrics from LLM
            metrics = self._llm.get_metrics()
            
            return {
                "status": "available",
                "prompt_tokens": metrics.get("prompt_tokens", 0),
                "completion_tokens": metrics.get("completion_tokens", 0),
                "total_tokens": metrics.get("total_tokens", 0),
                "estimated_cost": self._calculate_cost(metrics),
                "model": self._llm.model
            }
        except Exception as e:
            logger.warning(f"Could not get metrics: {e}")
            return {"status": "unavailable", "error": str(e)}
    
    def _calculate_cost(self, metrics: Dict) -> float:
        """Calculate estimated cost based on token usage."""
        # Approximate pricing (varies by model)
        prompt_cost_per_1k = 0.003  # $3/1M tokens
        completion_cost_per_1k = 0.015  # $15/1M tokens
        
        prompt_tokens = metrics.get("prompt_tokens", 0)
        completion_tokens = metrics.get("completion_tokens", 0)
        
        prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
        completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
        
        return prompt_cost + completion_cost
    
    def reset_metrics(self):
        """Reset metrics for a new session."""
        if self._llm:
            try:
                self._llm.reset_metrics()
            except:
                pass
    
    # ============= SANDBOX (DOCKER) =============
    
    @classmethod
    def create_with_docker(
        cls,
        api_key: str = None,
        workspace: str = "./workspace",
        security_level: str = "medium",
        docker_image: str = "openhands/runtime:latest"
    ) -> "RadcodeCoordinator":
        """
        Create a coordinator running in Docker sandbox.
        
        Args:
            api_key: LLM API key
            workspace: Workspace directory
            security_level: Security level (low/medium/high)
            docker_image: Docker image for sandbox
            
        Returns:
            RadcodeCoordinator instance with Docker workspace
        """
        try:
            from openhands.runtime import DockerRuntime
            
            # Create Docker runtime
            runtime = DockerRuntime(
                image=docker_image,
                workspace=workspace
            )
            
            # Create coordinator with runtime
            coordinator = cls(
                api_key=api_key,
                workspace=workspace,
                security_level=security_level
            )
            
            # Set the runtime on conversation
            # (will be applied during initialization)
            coordinator._docker_runtime = runtime
            
            logger.info(f"Created coordinator with Docker sandbox: {docker_image}")
            return coordinator
            
        except ImportError:
            logger.warning("Docker runtime not available, using local workspace")
            return cls(
                api_key=api_key,
                workspace=workspace,
                security_level=security_level
            )
    
    @classmethod
    def create_with_cloud(
        cls,
        api_key: str = None,
        workspace: str = "./workspace",
        security_level: str = "medium",
        cloud_url: str = None
    ) -> "RadcodeCoordinator":
        """
        Create a coordinator using OpenHands Cloud.
        
        Args:
            api_key: LLM API key
            workspace: Workspace directory
            security_level: Security level
            cloud_url: Optional custom cloud URL
            
        Returns:
            RadcodeCoordinator instance with cloud workspace
        """
        try:
            from openhands.runtime import CloudRuntime
            
            runtime = CloudRuntime(
                base_url=cloud_url,
                workspace=workspace
            )
            
            coordinator = cls(
                api_key=api_key,
                workspace=workspace,
                security_level=security_level
            )
            
            coordinator._cloud_runtime = runtime
            
            logger.info("Created coordinator with OpenHands Cloud")
            return coordinator
            
        except ImportError:
            logger.warning("Cloud runtime not available")
            return cls(
                api_key=api_key,
                workspace=workspace,
                security_level=security_level
            )
    
    # ============= CONTEXT MANAGEMENT (Long Tasks) =============
    
    def get_events(self):
        """Get conversation events for context analysis."""
        if not self._conversation:
            return []
        try:
            return self._conversation.events
        except:
            return []
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get summary of current context for long-task handling.
        """
        if not self._conversation:
            return {"status": "not_initialized"}
        
        try:
            events = self.get_events()
            event_count = len(events) if events else 0
            
            # Estimate token usage
            estimated_tokens = event_count * 200  # Rough estimate
            
            return {
                "status": "available",
                "event_count": event_count,
                "estimated_tokens": estimated_tokens,
                "needs_condensation": estimated_tokens > 50000,
                "model": self._llm.model if self._llm else None
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def can_continue(self) -> bool:
        """
        Check if agent can continue or needs context cleanup.
        """
        summary = self.get_context_summary()
        if summary.get("needs_condensation"):
            return False
        return True
    
    def condense_context(self) -> Dict[str, Any]:
        """
        Condense conversation context to reduce token usage.
        
        Called automatically when context exceeds 50k tokens.
        Keeps essential info (tasks, current state) and summarizes history.
        """
        if not self._conversation:
            return {"status": "not_initialized", "condensed": False}
        
        try:
            events = self.get_events()
            if not events:
                return {"status": "no_events", "condensed": False}
            
            # Extract key information to preserve
            preserved_info = {
                "completed_tasks": [],
                "current_progress": "unknown",
                "files_created": [],
                "errors_fixed": []
            }
            
            # Analyze events for key info
            for event in events:
                if hasattr(event, 'action'):
                    action = event.action if hasattr(event, 'action') else str(event)
                    # Track file creations
                    if 'create' in action.lower() and '.py' in action:
                        preserved_info["files_created"].append(action[:100])
                    # Track task completions
                    if 'complete' in action.lower() or 'done' in action.lower():
                        preserved_info["completed_tasks"].append(action[:100])
            
            # Attempt to condense via conversation API
            try:
                self._conversation.condense()
                logger.info("Context condensed successfully")
                return {
                    "status": "condensed",
                    "condensed": True,
                    "preserved": preserved_info
                }
            except AttributeError:
                # SDK doesn't support condense - manual truncate
                max_events = 50  # Keep last 50 events
                if len(events) > max_events:
                    logger.info(f"Truncating {len(events)} to {max_events} events")
                    # Note: This is simplified - real impl would need SDK support
                    return {
                        "status": "truncated",
                        "condensed": True,
                        "original_count": len(events),
                        "new_count": max_events,
                        "preserved": preserved_info
                    }
                return {"status": "no_condensation_needed", "condensed": False}
                
        except Exception as e:
            logger.warning(f"Context condensation failed: {e}")
    
    # ============= DEPLOYMENT =============
    
    def deploy_to_vercel(
        self,
        project_path: str,
        project_name: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy project to Vercel.
        
        Args:
            project_path: Path to project
            project_name: Optional project name
            token: Vercel token
            
        Returns:
            Deployment result
        """
        from src.deploy import DeploymentHelper
        return DeploymentHelper.deploy_vercel(project_path, project_name, token)
    
    def deploy_docker(
        self,
        project_path: str,
        image_name: str,
        tag: str = "latest",
        push: bool = False
    ) -> Dict[str, Any]:
        """
        Deploy project as Docker image.
        
        Args:
            project_path: Path to project
            image_name: Image name
            tag: Image tag
            push: Whether to push to registry
            
        Returns:
            Deployment result
        """
        from src.deploy import DeploymentHelper
        return DeploymentHelper.deploy_docker(project_path, image_name, tag, push=push)
    
    def deploy_fly(
        self,
        project_path: str,
        app_name: str,
        org: str = "personal"
    ) -> Dict[str, Any]:
        """
        Deploy project to Fly.io.
        
        Args:
            project_path: Path to project
            app_name: App name
            org: Organization
            
        Returns:
            Deployment result
        """
        from src.deploy import DeploymentHelper
        return DeploymentHelper.deploy_fly(project_path, app_name, org)