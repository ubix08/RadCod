"""
RadCode Admin API.

Comprehensive admin endpoints for agent management, workspaces, config, and monitoring.
"""

import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.coordinator import RadcodeCoordinator
from src.deploy import DeploymentHelper

logger = logging.getLogger("radcod.admin_api")

# ============= ROUTER =============

router = APIRouter(prefix="/api/v1", tags=["admin"])


# ============= MODELS =============


class TaskRequest(BaseModel):
    """Execute task request."""
    request: str = Field(..., min_length=1, max_length=10000)
    workspace: str = Field(default="default")
    security_level: str = Field(default="medium")
    model: Optional[str] = None
    timeout_seconds: int = Field(default=600, ge=60, le=3600)


class TaskResponse(BaseModel):
    """Task execution response."""
    task_id: str
    status: str
    created_at: float
    request: str
    workspace: str
    error: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """Task status response."""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    iterations: int = 0
    duration_seconds: float = 0.0
    created_at: float
    completed_at: Optional[float] = None


class WorkspaceCreate(BaseModel):
    """Create workspace."""
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    description: Optional[str] = None
    storage_path: Optional[str] = None


class WorkspaceResponse(BaseModel):
    """Workspace response."""
    name: str
    description: Optional[str] = None
    storage_path: str
    created_at: float
    task_count: int = 0


class WorkspaceListResponse(BaseModel):
    """List workspaces."""
    workspaces: List[WorkspaceResponse]
    total: int


class ConfigUpdate(BaseModel):
    """Update configuration."""
    security_level: Optional[str] = None
    model: Optional[str] = None
    timeout_seconds: Optional[int] = None


class ConfigResponse(BaseModel):
    """Configuration response."""
    security_level: str
    model: str
    timeout_default: int
    api_version: str


class MetricsResponse(BaseModel):
    """Metrics response."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    model: str
    tasks_completed: int
    tasks_failed: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: float
    active_tasks: int
    workspaces: int
    memory_mb: Optional[float] = None


class AgentStatusResponse(BaseModel):
    """Agent status."""
    status: str
    initialized: bool
    current_task: Optional[str] = None
    last_action: Optional[str] = None
    stuck_count: int = 0


class DiagnosticsResponse(BaseModel):
    """Diagnostics response."""
    python_version: str
    platform: str
    openhands_version: Optional[str] = None
    config_valid: bool
    config_errors: List[str] = []


# ============= STATE =============

# Task storage (in production, use Redis/DB)
_tasks: Dict[str, Dict] = {}

# Workspace storage
_workspaces: Dict[str, Dict] = {}

# Server start time
_start_time = time.time()


# ============= UTILITIES =============


def get_workspace_path(name: str) -> Path:
    """Get or create workspace path."""
    base = Path(os.getenv("RADCODE_WORKSPACES", "./workspaces"))
    ws_path = base / name
    ws_path.mkdir(parents=True, exist_ok=True)
    return ws_path


def check_api_key(request: Request) -> bool:
    """Check API key (simple version)."""
    # In production, implement proper auth
    api_key = request.headers.get("X-API-Key")
    expected = os.getenv("RADCODE_API_KEY")
    if expected and api_key != expected:
        return False
    return True


# ============= HEALTH =============


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    import psutil
    
    return HealthResponse(
        status="healthy",
        version="0.2.0",
        uptime_seconds=time.time() - _start_time,
        active_tasks=sum(1 for t in _tasks.values() if t.get("status") == "running"),
        workspaces=len(_workspaces),
        memory_mb=psutil.Process().memory_info().rss / 1024 / 1024
    )


@router.get("/diagnostics", response_model=DiagnosticsResponse)
async def diagnostics():
    """System diagnostics."""
    import sys
    
    diag = DiagnosticsResponse(
        python_version=sys.version.split()[0],
        platform=sys.platform,
        config_valid=True,
        config_errors=[]
    )
    
    # Check OpenHands
    try:
        import openhands
        diag.openhands_version = openhands.__version__
    except:
        pass
    
    # Check config
    if not os.getenv("LLM_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        diag.config_valid = False
        diag.config_errors.append("No LLM API key configured")
    
    return diag


# ============= TASKS =============


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    req: TaskRequest,
    background_tasks: BackgroundTasks
):
    """Create and execute a new task."""
    import asyncio
    
    # Validate workspace
    ws_path = get_workspace_path(req.workspace)
    
    # Create task
    task_id = str(uuid.uuid4())[:12]
    created_at = time.time()
    
    task = {
        "task_id": task_id,
        "status": "pending",
        "request": req.request,
        "workspace": req.workspace,
        "security_level": req.security_level,
        "model": req.model,
        "created_at": created_at,
        "result": None,
        "error": None,
        "iterations": 0,
        "duration": 0.0
    }
    
    _tasks[task_id] = task
    
    def run_task():
        """Execute task in background."""
        try:
            # Update status
            _tasks[task_id]["status"] = "running"
            
            # Create coordinator
            coord = RadcodeCoordinator(
                workspace=str(ws_path),
                security_level=req.security_level
            )
            
            # Override model if specified
            if req.model:
                os.environ["LLM_MODEL"] = req.model
            
            # Progress callback
            def on_progress(event: Dict):
                _tasks[task_id]["last_action"] = event.get("action", "")
            
            # Run with timeout
            result = coord.run(req.request, progress_callback=on_progress)
            
            # Store result
            _tasks[task_id]["status"] = result.get("status", "completed")
            _tasks[task_id]["result"] = result.get("result")
            _tasks[task_id]["error"] = result.get("error")
            _tasks[task_id]["iterations"] = result.get("iterations", 0)
            _tasks[task_id]["duration"] = time.time() - created_at
            _tasks[task_id]["completed_at"] = time.time()
            
            logger.info(f"Task {task_id} completed: {result.get('status')}")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            _tasks[task_id]["status"] = "failed"
            _tasks[task_id]["error"] = str(e)
            _tasks[task_id]["completed_at"] = time.time()
    
    # Schedule background execution
    background_tasks.add_task(run_task)
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        created_at=created_at,
        request=req.request,
        workspace=req.workspace
    )


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    workspace: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """List tasks with filters."""
    tasks = []
    
    for task_id, task in _tasks.items():
        # Filter by workspace
        if workspace and task.get("workspace") != workspace:
            continue
        # Filter by status
        if status and task.get("status") != status:
            continue
        
        tasks.append(TaskResponse(
            task_id=task_id,
            status=task["status"],
            created_at=task["created_at"],
            request=task["request"],
            workspace=task["workspace"]
        ))
        
        if len(tasks) >= limit:
            break
    
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str):
    """Get task status and result."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = _tasks[task_id]
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
        iterations=task.get("iterations", 0),
        duration_seconds=task.get("duration", 0.0),
        created_at=task["created_at"],
        completed_at=task.get("completed_at")
    )


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running task."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    _tasks[task_id]["status"] = "cancelled"
    _tasks[task_id]["completed_at"] = time.time()
    
    return {"status": "cancelled", "task_id": task_id}


# ============= WORKSPACES =============


@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(req: WorkspaceCreate):
    """Create a new workspace."""
    if req.name in _workspaces:
        raise HTTPException(status_code=409, detail="Workspace exists")
    
    storage = req.storage_path or str(get_workspace_path(req.name))
    
    workspace = {
        "name": req.name,
        "description": req.description,
        "storage_path": storage,
        "created_at": time.time(),
        "task_count": 0
    }
    
    _workspaces[req.name] = workspace
    
    return WorkspaceResponse(**workspace)


@router.get("/workspaces", response_model=WorkspaceListResponse)
async def list_workspaces():
    """List all workspaces."""
    workspaces = []
    
    for name, ws in _workspaces.items():
        # Count tasks for this workspace
        task_count = sum(1 for t in _tasks.values() if t.get("workspace") == name)
        ws_data = ws.copy()
        ws_data["task_count"] = task_count
        workspaces.append(WorkspaceResponse(**ws_data))
    
    return WorkspaceListResponse(
        workspaces=workspaces,
        total=len(workspaces)
    )


@router.get("/workspaces/{workspace}")
async def get_workspace(workspace: str):
    """Get workspace details."""
    if workspace not in _workspaces:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    ws = _workspaces[workspace]
    
    # Get tasks
    tasks = [
        {"task_id": k, "status": v["status"], "created_at": v["created_at"]}
        for k, v in _tasks.items()
        if v.get("workspace") == workspace
    ]
    
    return {
        **ws,
        "tasks": tasks,
        "task_count": len(tasks)
    }


@router.delete("/workspaces/{workspace}")
async def delete_workspace(workspace: str):
    """Delete a workspace."""
    if workspace not in _workspaces:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check for running tasks
    has_running = any(
        t.get("status") == "running"
        for t in _tasks.values()
        if t.get("workspace") == workspace
    )
    
    if has_running:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete workspace with running tasks"
        )
    
    del _workspaces[workspace]
    
    return {"status": "deleted", "workspace": workspace}


# ============= CONFIG =============


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get current configuration."""
    return ConfigResponse(
        security_level=os.getenv("RADCODE_SECURITY", "medium"),
        model=os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929"),
        timeout_default=int(os.getenv("RADCODE_TIMEOUT", "600")),
        api_version="v1"
    )


@router.patch("/config")
async def update_config(req: ConfigUpdate, request: Request):
    """Update configuration (runtime only)."""
    if not check_api_key(request):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if req.security_level:
        os.environ["RADCODE_SECURITY"] = req.security_level
    
    if req.model:
        os.environ["LLM_MODEL"] = req.model
    
    if req.timeout_seconds:
        os.environ["RADCODE_TIMEOUT"] = str(req.timeout_seconds)
    
    return {"status": "updated"}


# ============= METRICS =============


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(workspace: Optional[str] = None):
    """Get usage metrics."""
    # Aggregate metrics from coordinators
    total_prompt = 0
    total_completion = 0
    
    for task_id, task in _tasks.items():
        if workspace and task.get("workspace") != workspace:
            continue
        # This is simplified - real impl would track actual token usage
    
    completed = sum(1 for t in _tasks.values() if t.get("status") == "success")
    failed = sum(1 for t in _tasks.values() if t.get("status") == "failed")
    
    return MetricsResponse(
        prompt_tokens=total_prompt,
        completion_tokens=total_completion,
        total_tokens=total_prompt + total_completion,
        estimated_cost_usd=(total_prompt / 1_000_000 * 3) + (total_completion / 1_000_000 * 15),
        model=os.getenv("LLM_MODEL", "unknown"),
        tasks_completed=completed,
        tasks_failed=failed
    )


# ============= AGENT =============


@router.get("/agent/status", response_model=AgentStatusResponse)
async def get_agent_status(workspace: str = "default"):
    """Get agent status for workspace."""
    ws_path = get_workspace_path(workspace)
    
    try:
        coord = RadcodeCoordinator(workspace=str(ws_path))
        
        return AgentStatusResponse(
            status="ready" if coord._initialized else "idle",
            initialized=coord._initialized,
            current_task=None,
            last_action=None,
            stuck_count=0
        )
    except Exception as e:
        return AgentStatusResponse(
            status="error",
            initialized=False,
            last_action=str(e),
            stuck_count=0
        )


# ============= DEPLOY =============


@router.post("/deploy")
async def deploy_project(
    platform: str,
    project_path: str,
    name: str,
    token: Optional[str] = None,
    tag: str = "latest"
):
    """Deploy project to platform."""
    if platform == "vercel":
        result = DeploymentHelper.deploy_vercel(project_path, name, token)
    elif platform == "docker":
        result = DeploymentHelper.deploy_docker(project_path, name, tag)
    elif platform == "fly":
        result = DeploymentHelper.deploy_fly(project_path, name)
    elif platform == "render":
        result = DeploymentHelper.deploy_render(project_path, name, token)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
    
    return result


# ============= CONTEXT =============


@router.get("/context")
async def get_context(workspace: str = "default"):
    """Get context summary."""
    ws_path = get_workspace_path(workspace)
    
    try:
        coord = RadcodeCoordinator(workspace=str(ws_path))
        return coord.get_context_summary()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/context/condense")
async def condense_context(workspace: str = "default"):
    """Condense context."""
    ws_path = get_workspace_path(workspace)
    
    try:
        coord = RadcodeCoordinator(workspace=str(ws_path))
        return coord.condense_context()
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============= EXPORT ROUTER (for server.py) =============

__all__ = ["router"]