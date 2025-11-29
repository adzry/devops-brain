"""
Task Client

SDK client for task operations.
"""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from .exceptions import TaskError

if TYPE_CHECKING:
    from .client import DevOpsBrainClient


class TaskClient:
    """Client for task operations."""
    
    def __init__(self, client: "DevOpsBrainClient"):
        self._client = client
    
    async def list(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List tasks."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        result = await self._client._request("GET", "/api/v1/tasks", params=params)
        return result.get("tasks", [])
    
    async def get(self, task_id: str) -> dict:
        """Get task status."""
        return await self._client._request("GET", f"/api/v1/tasks/{task_id}")
    
    async def submit(
        self,
        action: str,
        payload: Optional[dict] = None,
        agent: Optional[str] = None,
        priority: str = "medium",
        timeout: int = 300,
    ) -> str:
        """
        Submit a task for async execution.
        
        Returns:
            Task ID
        """
        data = {
            "action": action,
            "payload": payload or {},
            "target_agent": agent,
            "priority": priority,
            "timeout_seconds": timeout,
        }
        
        result = await self._client._request("POST", "/api/v1/tasks/submit", data)
        return result["task_id"]
    
    async def execute(
        self,
        action: str,
        payload: Optional[dict] = None,
        agent: Optional[str] = None,
        priority: str = "medium",
        timeout: int = 300,
    ) -> dict:
        """Execute a task synchronously."""
        data = {
            "action": action,
            "payload": payload or {},
            "target_agent": agent,
            "priority": priority,
            "timeout_seconds": timeout,
        }
        
        return await self._client._request("POST", "/api/v1/tasks/execute", data)
    
    async def wait(
        self,
        task_id: str,
        timeout: int = 300,
        poll_interval: float = 1.0,
    ) -> dict:
        """Wait for a task to complete."""
        return await self._client._request(
            "POST",
            f"/api/v1/tasks/{task_id}/wait",
            params={"timeout": timeout},
        )
    
    async def poll(
        self,
        task_id: str,
        timeout: int = 300,
        interval: float = 2.0,
    ) -> dict:
        """Poll for task completion."""
        elapsed = 0
        
        while elapsed < timeout:
            result = await self.get(task_id)
            
            if result["status"] in ("completed", "failed", "cancelled"):
                if result["status"] == "failed":
                    raise TaskError(
                        result.get("error", "Task failed"),
                        task_id=task_id,
                    )
                return result
            
            await asyncio.sleep(interval)
            elapsed += interval
        
        raise TaskError(f"Task {task_id} timed out", task_id=task_id)
    
    async def workflow(
        self,
        tasks: list[dict],
        parallel: bool = False,
    ) -> dict:
        """Execute a workflow."""
        data = {"tasks": tasks, "parallel": parallel}
        return await self._client._request("POST", "/api/v1/tasks/workflow", data)
    
    # ========================================================================
    # Convenience Methods
    # ========================================================================
    
    async def run_and_wait(
        self,
        action: str,
        payload: Optional[dict] = None,
        agent: Optional[str] = None,
        timeout: int = 300,
    ) -> dict:
        """Submit task and wait for completion."""
        task_id = await self.submit(action, payload, agent)
        return await self.poll(task_id, timeout)
    
    async def batch(
        self,
        tasks: list[dict],
        parallel: bool = True,
    ) -> list[dict]:
        """
        Execute multiple tasks.
        
        Args:
            tasks: List of task dicts with 'action', 'payload', etc.
            parallel: Execute in parallel
            
        Returns:
            List of results
        """
        if parallel:
            # Submit all tasks
            task_ids = []
            for task in tasks:
                task_id = await self.submit(
                    action=task["action"],
                    payload=task.get("payload"),
                    agent=task.get("agent"),
                )
                task_ids.append(task_id)
            
            # Wait for all
            results = await asyncio.gather(
                *[self.poll(tid) for tid in task_ids],
                return_exceptions=True,
            )
            
            return [
                r if not isinstance(r, Exception) else {"error": str(r)}
                for r in results
            ]
        else:
            # Execute sequentially
            results = []
            for task in tasks:
                result = await self.execute(
                    action=task["action"],
                    payload=task.get("payload"),
                    agent=task.get("agent"),
                )
                results.append(result)
                
                if result.get("status") == "failed":
                    break
            
            return results
