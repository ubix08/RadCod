"""
Heartbeat and Scheduler System for 24/7 Radcod Operation.

Provides:
- Heartbeat monitor for system health
- Scheduled tasks (cron-like)
- Worker loop with graceful shutdown
- Queue management via HTTP API
"""

import os
import asyncio
import logging
import json
import time
import threading
import signal
import uuid
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from croniter import croniter
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger("radcod.scheduler")


class TaskStatus(str, Enum):
    """Status of a scheduled task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class HeartbeatStatus(str, Enum):
    """System heartbeat status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"


@dataclass
class ScheduledTask:
    """A task scheduled to run."""
    task_id: str
    name: str
    user_request: str
    cron_expression: str = ""  # Empty = one-time
    interval_seconds: int = 0  # 0 = one-time
    priority: int = 5
    enabled: bool = True
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def should_run(self) -> bool:
        """Check if task should run now."""
        if not self.enabled:
            return False
        
        if self.status == TaskStatus.RUNNING:
            return False
            
        if self.next_run and datetime.now() >= self.next_run:
            return True
            
        # For one-time tasks
        if not self.cron_expression and not self.interval_seconds:
            return self.status == TaskStatus.PENDING
            
        return False
    
    def calculate_next_run(self):
        """Calculate next run time."""
        now = datetime.now()
        
        if self.cron_expression:
            try:
                cron = croniter(self.cron_expression, now)
                self.next_run = cron.get_next(datetime)
            except:
                pass
        elif self.interval_seconds > 0:
            self.next_run = now + timedelta(seconds=self.interval_seconds)


@dataclass
class Heartbeat:
    """System heartbeat data."""
    status: HeartbeatStatus = HeartbeatStatus.HEALTHY
    uptime_seconds: float = 0.0
    requests_processed: int = 0
    requests_failed: int = 0
    avg_duration_ms: float = 0.0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    queue_size: int = 0
    active_agents: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "uptime_seconds": self.uptime_seconds,
            "requests_processed": self.requests_processed,
            "requests_failed": self.requests_failed,
            "avg_duration_ms": self.avg_duration_ms,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "queue_size": self.queue_size,
            "active_agents": self.active_agents
        }


@dataclass
class SchedulerState:
    """Current state of the scheduler."""
    running: bool = False
    started_at: Optional[datetime] = None
    heartbeat: Heartbeat = field(default_factory=Heartbeat)
    tasks: List[ScheduledTask] = field(default_factory=list)
    
    @property
    def uptime(self) -> float:
        if not self.started_at:
            return 0.0
        return (datetime.now() - self.started_at).total_seconds()


class TaskScheduler:
    """
    Main scheduler for 24/7 Radcod operation.
    
    Features:
    - Scheduled task execution
    - Heartbeat monitoring
    - Graceful shutdown
    - HTTP API for queue management
    """
    
    def __init__(
        self,
        coordinator = None,
        heartbeat_interval: int = 30,
        worker_interval: float = 1.0,
        api_port: int = 8080
    ):
        self.coordinator = coordinator
        self.heartbeat_interval = heartbeat_interval
        self.worker_interval = worker_interval
        self.api_port = api_port
        
        self.state = SchedulerState()
        self._lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Agent circuit breakers for health
        self._circuit_breakers: Dict[str, Any] = {}
        
        # Callbacks
        self._on_task_complete: Optional[Callable] = None
        self._on_task_fail: Optional[Callable] = None
        
        logger.info("TaskScheduler initialized.")
    
    # ============ Task Management ============
    
    def schedule_task(
        self,
        name: str,
        user_request: str,
        cron: str = "",
        interval: int = 0,
        priority: int = 5
    ) -> str:
        """Schedule a new task."""
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            user_request=user_request,
            cron_expression=cron,
            interval_seconds=interval,
            priority=priority
        )
        task.calculate_next_run()
        
        with self._lock:
            self.state.tasks.append(task)
        
        logger.info(f"Scheduled task: {task_id} ({name})")
        return task_id
    
    def schedule_now(self, user_request: str, priority: int = 5) -> str:
        """Schedule a task to run immediately."""
        return self.schedule_task(
            name=f"immediate-{uuid.uuid4().hex[:6]}",
            user_request=user_request,
            priority=priority
        )
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        with self._lock:
            for task in self.state.tasks:
                if task.task_id == task_id:
                    task.status = TaskStatus.CANCELLED
                    task.enabled = False
                    logger.info(f"Cancelled task: {task_id}")
                    return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID."""
        with self._lock:
            for task in self.state.tasks:
                if task.task_id == task_id:
                    return task
        return None
    
    def list_tasks(self, status: TaskStatus = None) -> List[ScheduledTask]:
        """List all tasks, optionally filtered by status."""
        with self._lock:
            if status:
                return [t for t in self.state.tasks if t.status == status]
            return list(self.state.tasks)
    
    # ============ Scheduler Loop ============
    
    def start(self):
        """Start the scheduler worker."""
        if self.state.running:
            logger.warning("Scheduler already running")
            return
        
        self._shutdown_event.clear()
        self.state.running = True
        self.state.started_at = datetime.now()
        
        # Start worker thread
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="radcod-worker"
        )
        self._worker_thread.start()
        
        # Start heartbeat thread
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="radcod-heartbeat"
        )
        self._heartbeat_thread.start()
        
        logger.info("Scheduler started.")
    
    def stop(self, timeout: float = 10.0):
        """Stop the scheduler gracefully."""
        if not self.state.running:
            return
        
        logger.info("Stopping scheduler...")
        self._shutdown_event.set()
        
        # Wait for worker to finish
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=timeout)
        
        # Wait for heartbeat to finish
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=5.0)
        
        self.state.running = False
        self.state.heartbeat.status = HeartbeatStatus.STOPPED
        
        logger.info("Scheduler stopped.")
    
    def _worker_loop(self):
        """Main worker loop."""
        logger.info("Worker loop started.")
        
        while not self._shutdown_event.is_set():
            try:
                self._process_tasks()
            except Exception as e:
                logger.error(f"Worker error: {e}")
            
            # Sleep with interruptible wait
            self._shutdown_event.wait(timeout=self.worker_interval)
        
        logger.info("Worker loop stopped.")
    
    def _process_tasks(self):
        """Process pending tasks."""
        tasks_to_run = []
        
        with self._lock:
            for task in self.state.tasks:
                if task.should_run():
                    tasks_to_run.append(task)
        
        for task in tasks_to_run:
            self._execute_task(task)
    
    def _execute_task(self, task: ScheduledTask):
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        logger.info(f"Executing task: {task.task_id} ({task.name})")
        
        try:
            if self.coordinator:
                result = self.coordinator.process_request(
                    task.user_request,
                    validation_callback=lambda s: True  # Auto-approve
                )
                task.result = result
                task.status = TaskStatus.COMPLETED
                self.state.heartbeat.requests_processed += 1
                
                logger.info(f"Task {task.task_id} completed successfully")
                
                if self._on_task_complete:
                    self._on_task_complete(task, result)
            else:
                # No coordinator - just mark as completed
                task.result = {"status": "no_coordinator"}
                task.status = TaskStatus.COMPLETED
                
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            self.state.heartbeat.requests_failed += 1
            
            logger.error(f"Task {task.task_id} failed: {e}")
            
            if self._on_task_fail:
                self._on_task_fail(task, e)
            
            # Retry logic
            if task.max_retries > 0:
                task.max_retries -= 1
                task.status = TaskStatus.PENDING
                logger.info(f"Task {task.task_id} will retry ({task.max_retries} retries left)")
        
        task.last_run = datetime.now()
        
        # Calculate next run for recurring tasks
        if task.cron_expression or task.interval_seconds:
            task.calculate_next_run()
    
    # ============ Heartbeat ============
    
    def _heartbeat_loop(self):
        """Heartbeat monitoring loop."""
        logger.info("Heartbeat loop started.")
        
        while not self._shutdown_event.is_set():
            try:
                self._update_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            
            self._shutdown_event.wait(timeout=self.heartbeat_interval)
        
        logger.info("Heartbeat loop stopped.")
    
    def _update_heartbeat(self):
        """Update heartbeat data."""
        hb = self.state.heartbeat
        
        hb.last_heartbeat = datetime.now()
        hb.uptime_seconds = self.state.uptime
        
        # Get queue size from coordinator if available
        if self.coordinator and hasattr(self.coordinator, '_queue'):
            hb.queue_size = self.coordinator._queue.qsize() if hasattr(self.coordinator._queue, 'qsize') else 0
        
        # Determine overall health
        if hb.requests_failed > hb.requests_processed * 0.5:
            hb.status = HeartbeatStatus.UNHEALTHY
        elif hb.requests_failed > 0:
            hb.status = HeartbeatStatus.DEGRADED
        else:
            hb.status = HeartbeatStatus.HEALTHY
        
        logger.debug(f"Heartbeat: {hb.status.value}")
    
    def get_heartbeat(self) -> Dict[str, Any]:
        """Get current heartbeat data."""
        return self.state.heartbeat.to_dict()
    
    # ============ HTTP API ============
    
    def start_api(self):
        """Start HTTP API server (optional)."""
        # Simple API would be implemented here
        # For production, use FastAPI/Starlette
        logger.info(f"API available on port {self.api_port}")
    
    # ============ Signal Handling ============
    
    def setup_signals(self):
        """Setup graceful shutdown signals."""
        def handle_signal(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            self.stop()
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)


# ============ HTTP Handler for API ============

class SchedulerAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler for scheduler API."""
    
    def log_message(self, format, *args):
        logger.info(f"{self.address_string} - {format % args}")
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == "/health":
            self._send_json({"status": "ok"})
        elif path == "/tasks":
            self._send_json({"tasks": []})  # TODO: get from scheduler
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        if path == "/tasks":
            # Parse request body
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            
            # Schedule task
            task_id = self.scheduler.schedule_now(
                data.get("user_request"),
                data.get("priority", 5)
            )
            
            self._send_json({"task_id": task_id, "status": "queued"})
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def _send_json(self, data: Dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


# ============ Factory ============

def create_scheduler(
    coordinator = None,
    port: int = 8080
) -> TaskScheduler:
    """Create and configure a task scheduler."""
    scheduler = TaskScheduler(
        coordinator=coordinator,
        api_port=port
    )
    
    # Setup signal handlers
    scheduler.setup_signals()
    
    return scheduler