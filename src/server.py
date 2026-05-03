"""
RadCode FastAPI Server.

Provides REST API for autonomous agent execution.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.coordinator import RadcodeCoordinator
from src.deploy import DeploymentHelper
from src.api import router as admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("radcod.server")


# ============= REQUEST/RESPONSE MODELS =============


class RunRequest(BaseModel):
    """Request to run a task."""
    request: str = Field(..., description="Task request or prompt")
    workspace: str = Field(default="./workspace", description="Working directory")
    security_level: str = Field(default="medium", description="Security level")
    timeout_seconds: int = Field(default=600, description="Max execution time")
    model: Optional[str] = Field(default=None, description="LLM model override")


class RunResponse(BaseModel):
    """Response from task execution."""
    status: str  # success, error, timeout
    request: str
    result: Optional[Any] = None
    error: Optional[str] = None
    iterations: int = 0
    duration_seconds: float = 0.0
    security_level: str


class MetricsResponse(BaseModel):
    """Metrics response."""
    status: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    model: str = ""


class DeployRequest(BaseModel):
    """Deployment request."""
    platform: str = Field(..., description="vercel, docker, fly, render")
    project_path: str = Field(..., description="Path to project")
    name: str = Field(..., description="Project/app name")
    token: Optional[str] = Field(default=None, description="API token")
    tag: str = Field(default="latest", description="Docker tag")
    push: bool = Field(default=False, description="Push to registry")


class DeployResponse(BaseModel):
    """Deployment response."""
    status: str
    url: Optional[str] = None
    image: Optional[str] = None
    error: Optional[str] = None


# ============= GLOBAL STATE =============

# Active coordinators per workspace
_coordinators: Dict[str, RadcodeCoordinator] = {}

# WebSocket connections for progress
_progress_connections: List[WebSocket] = []


def get_coordinator(workspace: str = "./workspace") -> RadcodeCoordinator:
    """Get or create coordinator for workspace."""
    if workspace not in _coordinators:
        _coordinators[workspace] = RadcodeCoordinator(workspace=workspace)
    return _coordinators[workspace]


# ============= LIFECYCLE =============


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    logger.info("Starting RadCode server...")
    yield
    logger.info("Shutting down RadCode server...")


# ============= SERVER =============


app = FastAPI(
    title="RadCode API",
    description="Autonomous AI Software Engineer API",
    version="0.2.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include admin API router
app.include_router(admin_router)


# ============= ROOT =============


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "RadCode API",
        "version": "0.2.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


# ============= RUN =============


@app.post("/run", response_model=RunResponse)
async def run_task(req: RunRequest, background_tasks: BackgroundTasks):
    """
    Execute a task using the autonomous agent.
    
    This runs asynchronously and returns immediately with a task ID.
    Use /run/{task_id} to check status, or WebSocket for progress.
    """
    import time
    import uuid
    
    task_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    def execute_task():
        """Background task execution."""
        try:
            coord = get_coordinator(req.workspace)
            
            # Set security level
            coord._security_level = req.security_level
            
            # Override model if provided
            if req.model:
                coord._llm.model = req.model
            
            # Run with progress broadcast
            def on_progress(event: Dict):
                # Broadcast to WebSocket (sync-safe)
                for ws in _progress_connections:
                    try:
                        # Use thread-safe send
                        import asyncio
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.call_soon_threadsafe(
                                ws.send_json,
                                {"task_id": task_id, **event}
                            )
                    except Exception:
                        pass
            
            result = coord.run(req.request, progress_callback=on_progress)
            
            # Store result 
            _coordinators[f"{req.workspace}:{task_id}"] = {
                "status": result.get("status", "unknown"),
                "result": result.get("result"),
                "error": result.get("error"),
                "iterations": result.get("iterations", 0),
                "duration": time.time() - start_time
            }
            
            logger.info(f"Task {task_id} completed: {result.get('status')}")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            _coordinators[f"{req.workspace}:{task_id}"] = {
                "status": "error",
                "error": str(e)
            }
    
    # Schedule background execution
    background_tasks.add_task(execute_task)
    
    return RunResponse(
        status="started",
        request=req.request,
        iterations=0,
        duration_seconds=0.0,
        security_level=req.security_level
    )


# ============= STATUS =============


@app.get("/run/{task_id}")
async def get_task_status(task_id: str, workspace: str = "./workspace"):
    """Get status of a running task."""
    key = f"{workspace}:{task_id}"
    if key not in _coordinators:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return _coordinators[key]


# ============= METRICS =============


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(workspace: str = "./workspace"):
    """Get current metrics."""
    coord = get_coordinator(workspace)
    metrics = coord.get_metrics()
    
    return MetricsResponse(
        status=metrics.get("status", "unavailable"),
        prompt_tokens=metrics.get("prompt_tokens", 0),
        completion_tokens=metrics.get("completion_tokens", 0),
        total_tokens=metrics.get("total_tokens", 0),
        estimated_cost=metrics.get("estimated_cost", 0.0),
        model=metrics.get("model", "")
    )


# ============= CONTEXT =============


@app.get("/context")
async def get_context(workspace: str = "./workspace"):
    """Get context summary."""
    coord = get_coordinator(workspace)
    return coord.get_context_summary()


@app.post("/context/condense")
async def condense_context(workspace: str = "./workspace"):
    """Condense context for long tasks."""
    coord = get_coordinator(workspace)
    return coord.condense_context()


# ============= DEPLOY =============


@app.post("/deploy", response_model=DeployResponse)
async def deploy(req: DeployRequest):
    """Deploy project to platform."""
    if req.platform == "vercel":
        result = DeploymentHelper.deploy_vercel(req.project_path, req.name, req.token)
    elif req.platform == "docker":
        result = DeploymentHelper.deploy_docker(req.project_path, req.name, req.tag, push=req.push)
    elif req.platform == "fly":
        result = DeploymentHelper.deploy_fly(req.project_path, req.name)
    elif req.platform == "render":
        result = DeploymentHelper.deploy_render(req.project_path, req.name, req.token)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {req.platform}")
    
    return DeployResponse(
        status=result.get("status", "error"),
        url=result.get("url"),
        image=result.get("image"),
        error=result.get("error")
    )


# ============= WEBSOCKET =============


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time progress."""
    await websocket.accept()
    _progress_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive, receive messages
            data = await websocket.receive_text()
            
            # Handle commands
            try:
                import json
                msg = json.loads(data)
                
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg.get("type") == "cancel":
                    # Cancel task - requires implementation
                    await websocket.send_json({"status": "cancelled"})
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _progress_connections:
            _progress_connections.remove(websocket)


# ============= STANDALONE =============


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )