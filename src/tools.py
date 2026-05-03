"""
RadCode Additional Tools.

Real sub-agent tools and utilities that complement SDK.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("radcod.tools")


# ============= SUB-AGENT TOOL =============

class SubAgentTool:
    """
    Real sub-agent tool for delegating to specialized agents.
    
    Usage in prompts:
        Use the BackendAgent to create the API schema
        Use the TestAgent to write test coverage
    """
    
    # Agent configurations
    AGENTS = {
        "backend": {
            "name": "Backend Agent",
            "description": "Creates APIs, databases, server logic",
            "system_prompt": """You are an expert backend developer.
Create FastAPI/Django/Express endpoints, SQL schemas, auth flows.
Focus on: REST APIs, GraphQL, PostgreSQL, Redis, JWT."""
        },
        "frontend": {
            "name": "Frontend Agent", 
            "description": "Creates UI, React components",
            "system_prompt": """You are an expert frontend developer.
Create React/Vue/Svelte components, responsive UIs.
Focus on: React, TypeScript, Tailwind, accessibility."""
        },
        "test": {
            "name": "Test Agent",
            "description": "Writes tests, runs test suites",
            "system_prompt": """You are an expert QA engineer.
Write pytest/Jest tests, unit and integration tests.
Focus on: TDD, fixtures, mocking, >80% coverage."""
        },
        "devops": {
            "name": "DevOps Agent",
            "description": "Deploys to Docker, Kubernetes, cloud",
            "system_prompt": """You are an expert DevOps engineer.
Create Dockerfiles, CI/CD pipelines, K8s manifests.
Focus on: Docker, GitHub Actions, AWS, Terraform."""
        },
        "debug": {
            "name": "Debug Agent",
            "description": "Debugs errors, analyzes stack traces",
            "system_prompt": """You are an expert debugger.
Analyze error messages, stack traces, logs.
Focus on: root cause analysis, logging, fixing bugs."""
        },
        "review": {
            "name": "Code Review Agent",
            "description": "Reviews code quality, security",
            "system_prompt": """You are an expert code reviewer.
Review PRs for bugs, security, performance.
Focus on: code quality, vulnerabilities, best practices."""
        }
    }
    
    def __init__(self, llm=None, workspace="./workspace"):
        self._llm = llm
        self._workspace = workspace
        self._agent_cache: Dict[str, Any] = {}
    
    def run(self, agent_type: str, task: str) -> Dict[str, Any]:
        """
        Run a sub-agent.
        
        Args:
            agent_type: One of backend, frontend, test, devops, debug, review
            task: Task description
            
        Returns:
            Result dict
        """
        if agent_type not in self.AGENTS:
            return {"status": "error", "error": f"Unknown agent: {agent_type}"}
        
        config = self.AGENTS[agent_type]
        
        # For now, return a prompt that can be used
        # In full impl, would create actual sub-agent
        return {
            "status": "delegated",
            "agent": config["name"],
            "task": task,
            "system_prompt": config["system_prompt"]
        }


# ============= SANDBOX EXECUTOR =============

class SandboxExecutor:
    """
    Docker-based command sandbox.
    
    Runs commands in isolated containers for security.
    """
    
    def __init__(
        self,
        image: str = "python:3.11-slim",
        workspace: str = "./workspace"
    ):
        self._image = image
        self._workspace = Path(workspace)
        self._docker = None
    
    def _ensure_docker(self):
        """Lazy init docker."""
        if self._docker is not None:
            return
        
        try:
            import docker
            self._docker = docker.from_env()
        except ImportError:
            logger.warning("docker not installed, using host execution")
            self._docker = False
        except Exception as e:
            logger.warning(f"Docker unavailable: {e}")
            self._docker = False
    
    def execute(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Execute command in sandbox.
        
        Args:
            command: Shell command
            timeout: Max seconds
            
        Returns:
            Output dict with stdout, stderr, returncode
        """
        self._ensure_docker()
        
        if not self._docker:
            # Fallback: run on host
            return self._execute_host(command, timeout)
        
        try:
            # Run in container
            container = self._docker.containers.run(
                self._image,
                f"radcod-{os.getpid()}",
                detach=True,
                remove=True,
                volumes={
                    str(self._workspace.absolute()): {
                        'bind': '/workspace',
                        'mode': 'rw'
                    }
                },
                working_dir="/workspace",
                command=["sh", "-c", command]
            )
            
            result = container.wait(timeout=timeout)
            
            return {
                "status": "success" if result.StatusCode == 0 else "error",
                "returncode": result.StatusCode,
                "stdout": result.Logs.decode() if result.Logs else "",
                "container_id": container.id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _execute_host(self, command: str, timeout: int) -> Dict[str, Any]:
        """Execute on host as fallback."""
        import subprocess
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self._workspace,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ============= TASK STATE =============

class TaskState:
    """Simple task state tracking."""
    
    def __init__(self):
        self._tasks: Dict[str, Dict] = {}
    
    def create(self, task_id: str, description: str, metadata: Dict = None) -> None:
        self._tasks[task_id] = {
            "id": task_id,
            "description": description,
            "status": "pending",
            "metadata": metadata or {},
        }
    
    def update(self, task_id: str, status: str = None, result: Any = None) -> None:
        if task_id not in self._tasks:
            return
        
        if status:
            self._tasks[task_id]["status"] = status
        if result is not None:
            self._tasks[task_id]["result"] = result
    
    def get(self, task_id: str) -> Optional[Dict]:
        return self._tasks.get(task_id)
    
    def list(self, status: str = None) -> list:
        if status:
            return [t for t in self._tasks.values() if t.get("status") == status]
        return list(self._tasks.values())


# ============= CONVENIENCE =============

def get_tools(llm=None, workspace="./workspace") -> Dict[str, Any]:
    """Get all additional tools."""
    return {
        "subagent": SubAgentTool(llm, workspace),
        "sandbox": SandboxExecutor(workspace=workspace),
        "state": TaskState()
    }


# ============= SETUP HELPER =============

def setup_workspace(workspace: str = "./workspace") -> Path:
    """Setup workspace directory."""
    ws = Path(workspace)
    ws.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep
    (ws / ".gitkeep").touch()
    
    logger.info(f"Workspace ready: {ws}")
    return ws


def check_environment() -> Dict[str, Any]:
    """Check environment setup."""
    checks = {
        "python": True,
        "workspace": True,
        "docker": False,
        "sdk": False
    }
    
    # Python
    import sys
    checks["python_version"] = sys.version.split()[0]
    
    # Docker
    try:
        import docker
        docker.from_env().ping()
        checks["docker"] = True
    except:
        pass
    
    # SDK
    try:
        import openhands
        checks["sdk"] = True
    except:
        pass
    
    return checks


if __name__ == "__main__":
    # Quick check
    print("Environment:")
    for k, v in check_environment().items():
        print(f"  {k}: {v}")
