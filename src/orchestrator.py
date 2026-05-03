"""
RadCode Orchestrator - Multi-Agent Architecture.

Implements Devin-like orchestrator pattern:
- Task decomposition into subtasks
- Sub-agent spawning for parallel execution
- Result aggregation

Use:
    from src.orchestrator import RadCodeOrchestrator
    
    orchestrator = RadCodeOrchestrator()
    result = orchestrator.run("Build a full-stack CRM app")
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("radcod.orchestrator")


class SubTaskStatus(Enum):
    """Subtask execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubTask:
    """Represents a decomposed subtask."""
    id: str
    name: str
    description: str
    workspace: str
    dependencies: List[str] = field(default_factory=list)
    status: SubTaskStatus = SubTaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "workspace": self.workspace,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class OrchestratorConfig:
    """Configuration for orchestrator."""
    max_parallel_agents: int = 4
    decomposition_prompt: str = """
You are a task decomposition expert. Break down the user's request into independent subtasks.
Each subtask should be:
1. Independent (no dependencies on other subtasks)
2. Can run in parallel with other subtasks
3. Has clear deliverables

Respond with a JSON array of subtasks, each with:
- name: short descriptive name
- description: what this subtask does
- workspace: directory for this subtask (create if needed)
- dependencies: list of subtask IDs this depends on (empty if none)

Example decomposition for "Build a full-stack CRM":
[
  {"name": "backend", "description": "Create FastAPI backend with CRUD for contacts", "workspace": "./backend", "dependencies": []},
  {"name": "frontend", "description": "Create React dashboard UI", "workspace": "./frontend", "dependencies": ["backend"]},
  {"name": "tests", "description": "Write integration tests", "workspace": "./tests", "dependencies": ["backend", "frontend"]}
]
"""
    aggregation_prompt: str = """
You are a result aggregator. Combine the results from multiple subtasks into a coherent final result.
Provide a summary of what was accomplished and any issues encountered.
"""
    default_workspace: str = "./workspace"


class RadCodeOrchestrator:
    """
    Multi-agent orchestrator for complex tasks.
    
    Architecture:
    1. Decompose task into subtasks (LLM)
    2. Spawn sub-agents for each subtask
    3. Run in parallel (respecting dependencies)
    4. Aggregate results
    
    Usage:
        orchestrator = RadCodeOrchestrator()
        result = orchestrator.run("Build a full-stack app")
    """
    
    def __init__(
        self,
        security_level: str = "medium",
        config: Optional[OrchestratorConfig] = None,
        **kwargs
    ):
        """
        Initialize orchestrator.
        
        Args:
            security_level: Security level (low/medium/high)
            config: Optional orchestrator config
            **kwargs: Passed to sub-agents
        """
        self._security_level = security_level
        self._config = config or OrchestratorConfig()
        self._kwargs = kwargs
        self._subtasks: Dict[str, SubTask] = {}
        self._agents: Dict[str, Any] = {}
        self._coordinator_initialized = False
    
    def _get_coordinator(self):
        """Lazy import and cache coordinator."""
        if not self._coordinator_initialized:
            from src.coordinator import RadcodeCoordinator
            self._Coordinator = RadcodeCoordinator
            self._coordinator_initialized = True
        return self._Coordinator
    
    def decompose(self, task: str) -> List[SubTask]:
        """
        Decompose a complex task into subtasks.
        
        Uses LLM to generate subtask list.
        
        Args:
            task: The complex task to decompose
            
        Returns:
            List of SubTask objects
        """
        import json
        import uuid
        
        # Get Coordinator for LLM access
        Coordinator = self._get_coordinator()
        
        # Create a simple coordinator for decomposition
        coord = Coordinator(security_level=self._security_level)
        
        # Ask LLM to decompose
        prompt = f"{self._config.decomposition_prompt}\n\nTask: {task}"
        
        logger.info(f"Decomposing task: {task[:100]}...")
        
        try:
            # Send to conversation
            coord.conversation.send_message(prompt)
            response = ""
            
            # Stream response
            for event in coord.conversation.stream_events():
                if hasattr(event, 'observation') and event.observation:
                    obs = event.observation
                    if hasattr(obs, 'content') and obs.content:
                        response += str(obs.content)
            
            # Parse JSON from response
            # Try to extract JSON array
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                subtask_data = json.loads(json_str)
            else:
                # Try whole response
                subtask_data = json.loads(response)
            
            # Convert to SubTask objects
            subtasks = []
            for i, data in enumerate(subtask_data):
                subtask = SubTask(
                    id=f"subtask-{i}",
                    name=data.get("name", f"task-{i}"),
                    description=data.get("description", ""),
                    workspace=data.get("workspace", f"{self._config.default_workspace}/subtask-{i}"),
                    dependencies=data.get("dependencies", []),
                )
                subtasks.append(subtask)
            
            logger.info(f"Decomposed into {len(subtasks)} subtasks: {[s.name for s in subtasks]}")
            return subtasks
            
        except Exception as e:
            logger.warning(f"Decomposition failed: {e}, falling back to single task")
            # Fallback: single task
            return [
                SubTask(
                    id="subtask-0",
                    name="main",
                    description=task,
                    workspace=self._config.default_workspace,
                    dependencies=[],
                )
            ]
    
    def _spawn_agent(self, subtask: SubTask):
        """Spawn an agent for a subtask."""
        from src.coordinator import RadcodeCoordinator
        
        # Create workspace
        workspace = subtask.workspace
        os.makedirs(workspace, exist_ok=True)
        
        # Create agent
        agent = RadcodeCoordinator(
            workspace=workspace,
            security_level=self._security_level,
            **self._kwargs
        )
        
        return agent
    
    def _can_run(self, subtask: SubTask) -> bool:
        """Check if subtask dependencies are satisfied."""
        for dep_id in subtask.dependencies:
            # Check if dependency exists
            if dep_id not in self._subtasks:
                logger.warning(f"Unknown dependency: {dep_id} for {subtask.name}")
                return False
            
            dep = self._subtasks.get(dep_id)
            if dep and dep.status != SubTaskStatus.SUCCESS:
                return False
        return True
    
    async def _run_subtask_async(self, subtask: SubTask) -> SubTask:
        """Run a single subtask asynchronously."""
        logger.info(f"Running subtask: {subtask.name}")
        
        # Check dependencies
        if not self._can_run(subtask):
            subtask.status = SubTaskStatus.CANCELLED
            subtask.error = "Dependencies not satisfied"
            return subtask
        
        try:
            # Spawn agent
            agent = self._spawn_agent(subtask)
            self._agents[subtask.id] = agent
            
            # Run task
            result = await asyncio.wait_for(
                asyncio.to_thread(agent.run, subtask.description),
                timeout=600
            )
            
            subtask.result = result
            subtask.status = SubTaskStatus.SUCCESS
            logger.info(f"Subtask {subtask.name} completed")
            
        except asyncio.TimeoutError:
            subtask.status = SubTaskStatus.FAILED
            subtask.error = "Timeout"
            logger.error(f"Subtask {subtask.name} timed out")
            
        except Exception as e:
            subtask.status = SubTaskStatus.FAILED
            subtask.error = str(e)
            logger.error(f"Subtask {subtask.name} failed: {e}")
        
        return subtask
    
    def _run_subtask_sync(self, subtask: SubTask) -> SubTask:
        """Run a single subtask synchronously."""
        logger.info(f"Running subtask: {subtask.name}")
        
        # Check dependencies
        if not self._can_run(subtask):
            subtask.status = SubTaskStatus.CANCELLED
            subtask.error = "Dependencies not satisfied"
            return subtask
        
        try:
            # Spawn agent
            agent = self._spawn_agent(subtask)
            self._agents[subtask.id] = agent
            
            # Run task (blocking)
            result = agent.run(subtask.description)
            
            subtask.result = result
            subtask.status = SubTaskStatus.SUCCESS
            logger.info(f"Subtask {subtask.name} completed")
            
        except Exception as e:
            subtask.status = SubTaskStatus.FAILED
            subtask.error = str(e)
            logger.error(f"Subtask {subtask.name} failed: {e}")
        
        return subtask
    
    def run(self, task: str, parallel: bool = True, timeout_seconds: int = 600) -> Dict[str, Any]:
        """
        Execute a complex task using multi-agent orchestration.
        
        Args:
            task: The task to execute
            parallel: Run independent subtasks in parallel
            timeout_seconds: Max time for entire orchestration (default 10 min, max 30 min)
            
        Returns:
            Dict with results and metadata
        """
        import uuid
        import time
        
        # Enforce timeout (max 30 minutes)
        timeout = min(timeout_seconds, 1800)
        start_time = time.time()
        
        # Step 1: Decompose
        subtasks = self.decompose(task)
        
        # Store subtasks
        for st in subtasks:
            self._subtasks[st.id] = st
        
        # Step 2: Execute
        if parallel:
            results = self._run_parallel(subtasks)
        else:
            results = self._run_sequential(subtasks)
        
        # Step 3: Aggregate
        final_result = self.aggregate(results)
        
        # Check timeout
        elapsed = time.time() - start_time
        timed_out = elapsed > timeout
        
        return {
            "status": "timeout" if timed_out else ("success" if all(s.status == SubTaskStatus.SUCCESS for s in results) else "partial"),
            "task": task,
            "subtasks": [s.to_dict() for s in results],
            "result": final_result,
            "total_subtasks": len(subtasks),
            "successful": sum(1 for s in results if s.status == SubTaskStatus.SUCCESS),
            "failed": sum(1 for s in results if s.status == SubTaskStatus.FAILED),
            "duration_seconds": elapsed,
            "timeout": timed_out,
        }
    
    def _run_sequential(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Run subtasks sequentially (simple but slow)."""
        results = []
        for subtask in subtasks:
            result = self._run_subtask_sync(subtask)
            results.append(result)
        return results
    
    def _run_parallel(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Run subtasks in parallel, respecting dependencies."""
        import concurrent.futures
        
        results = []
        pending = list(subtasks)  # Track pending
        max_workers = self._config.max_parallel_agents
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            while pending or futures:
                # Find ready subtasks (dependencies satisfied and not yet run)
                ready = [s for s in pending if self._can_run(s)]
                
                # Submit ready tasks (up to max workers)
                for subtask in ready[:max_workers - len(futures)]:
                    future = executor.submit(self._run_subtask_sync, subtask)
                    futures[future] = subtask
                    pending.remove(subtask)
                
                if not futures:
                    # Nothing can run - check if blocked or done
                    if pending:
                        logger.warning(f"Blocked subtasks remaining: {len(pending)}")
                        # Move one blocked task to results with cancelled status
                        blocked = pending.pop(0)
                        blocked.status = SubTaskStatus.CANCELLED
                        blocked.error = "Dependencies cannot be satisfied"
                        results.append(blocked)
                    break
                
                # Wait for any to complete
                done, _ = concurrent.futures.wait(
                    futures.keys(), 
                    return_when=concurrent.futures.FIRST_COMPLETED
                )
                
                for future in done:
                    subtask = futures.pop(future)
                    results.append(subtask)
                    
                    # Propagate failure to dependents
                    if subtask.status == SubTaskStatus.FAILED:
                        self._propagate_failure(subtask)
        
        return results
    
    def _propagate_failure(self, failed_subtask: SubTask):
        """Cancel dependent subtasks when a dependency fails."""
        for subtask in self._subtasks.values():
            if failed_subtask.id in subtask.dependencies:
                subtask.status = SubTaskStatus.CANCELLED
                subtask.error = f"Dependency {failed_subtask.name} failed"
    
    def aggregate(self, results: List[SubTask]) -> Dict[str, Any]:
        """Aggregate results from subtasks."""
        # Create summary
        success_count = sum(1 for r in results if r.status == SubTaskStatus.SUCCESS)
        failed_count = sum(1 for r in results if r.status == SubTaskStatus.FAILED)
        
        summary = {
            "total": len(results),
            "successful": success_count,
            "failed": failed_count,
            "subtasks": [
                {"name": r.name, "status": r.status.value, "error": r.error}
                for r in results
            ]
        }
        
        # If all succeeded
        if success_count == len(results):
            summary["status"] = "success"
            summary["message"] = f"All {success_count} subtasks completed successfully"
        elif success_count > 0:
            summary["status"] = "partial"
            summary["message"] = f"{success_count} succeeded, {failed_count} failed"
        else:
            summary["status"] = "failed"
            summary["message"] = "All subtasks failed"
        
        return summary
    
    @property
    def subtasks(self) -> Dict[str, SubTask]:
        """Get all subtasks."""
        return self._subtasks
    
    @property
    def agents(self) -> Dict[str, Any]:
        """Get all spawned agents."""
        return self._agents


# ===== CLI INTEGRATION =====

def main():
    """CLI for orchestrator."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.orchestrator <task>")
        print("Example: python -m src.orchestrator 'Build a full-stack CRM with React and FastAPI'")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    
    orchestrator = RadCodeOrchestrator()
    result = orchestrator.run(task)
    
    print(f"\n=== Result ===")
    print(f"Status: {result['status']}")
    print(f"Subtasks: {result['successful']}/{result['total_subtasks']} succeeded")
    print(f"\n{result['result']}")


if __name__ == "__main__":
    main()