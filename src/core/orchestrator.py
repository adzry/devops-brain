"""
Agent Orchestrator

Central coordination layer that routes tasks to appropriate specialist agents,
manages agent lifecycle, and handles inter-agent communication.
"""

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .message_queue import MessageQueue, Message, MessagePriority

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskRequest:
    """Represents a task request to the orchestrator."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    target_agent: Optional[str] = None
    priority: MessagePriority = MessagePriority.MEDIUM
    timeout_seconds: int = 300
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of a task execution."""
    
    task_id: str
    status: TaskStatus
    agent: str
    action: str
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """Registry for managing agent instances."""
    
    def __init__(self):
        self._agents: dict[str, Any] = {}
        self._capabilities: dict[str, list[str]] = {}
    
    def register(self, name: str, agent: Any, capabilities: list[str]) -> None:
        """Register an agent with its capabilities."""
        self._agents[name] = agent
        self._capabilities[name] = capabilities
        logger.info(f"Registered agent: {name} with capabilities: {capabilities}")
    
    def unregister(self, name: str) -> None:
        """Unregister an agent."""
        self._agents.pop(name, None)
        self._capabilities.pop(name, None)
        logger.info(f"Unregistered agent: {name}")
    
    def get(self, name: str) -> Optional[Any]:
        """Get an agent by name."""
        return self._agents.get(name)
    
    def get_by_capability(self, capability: str) -> list[str]:
        """Get agent names that have a specific capability."""
        return [
            name for name, caps in self._capabilities.items()
            if capability in caps
        ]
    
    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents."""
        return [
            {
                "name": name,
                "capabilities": self._capabilities.get(name, []),
                "status": "active" if agent else "inactive",
            }
            for name, agent in self._agents.items()
        ]


class Orchestrator:
    """
    Central orchestrator for coordinating agent tasks.
    
    Responsibilities:
    - Route tasks to appropriate agents
    - Manage agent lifecycle
    - Handle task queuing and prioritization
    - Track task execution status
    - Coordinate multi-agent workflows
    """
    
    # Routing patterns for automatic agent selection
    ROUTING_PATTERNS = [
        (r"security|vulnerability|CVE|secret|compliance", "security_agent"),
        (r"test|coverage|spec|assertion", "testing_agent"),
        (r"document|readme|changelog|api.?doc", "documentation_agent"),
        (r"performance|latency|throughput|profile|optimize", "performance_agent"),
        (r"incident|outage|alert|pager|sev[1-4]", "incident_response_agent"),
        (r"database|migration|schema|query|index|sql", "database_agent"),
        (r"infrastructure|terraform|kubernetes|k8s|cloud|aws|gcp", "infrastructure_agent"),
        (r"deploy|release|rollback|pipeline", "deployment_agent"),
        (r"review|analyze|check", "code_review_agent"),
    ]
    
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        default_timeout: int = 300,
    ):
        self.registry = AgentRegistry()
        self.message_queue = MessageQueue()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = default_timeout
        
        self._tasks: dict[str, TaskResult] = {}
        self._running_tasks: set[str] = set()
        self._lock = asyncio.Lock()
        self._shutdown = False
        
        logger.info("Orchestrator initialized")
    
    async def start(self) -> None:
        """Start the orchestrator and begin processing tasks."""
        self._shutdown = False
        logger.info("Orchestrator started")
        asyncio.create_task(self._process_queue())
    
    async def stop(self) -> None:
        """Stop the orchestrator gracefully."""
        self._shutdown = True
        logger.info("Orchestrator stopping...")
        
        # Wait for running tasks to complete
        while self._running_tasks:
            await asyncio.sleep(0.1)
        
        logger.info("Orchestrator stopped")
    
    def register_agent(
        self,
        name: str,
        agent: Any,
        capabilities: list[str],
    ) -> None:
        """Register an agent with the orchestrator."""
        self.registry.register(name, agent, capabilities)
    
    def unregister_agent(self, name: str) -> None:
        """Unregister an agent."""
        self.registry.unregister(name)
    
    async def submit_task(self, request: TaskRequest) -> str:
        """
        Submit a task for execution.
        
        Args:
            request: The task request
            
        Returns:
            Task ID for tracking
        """
        # Determine target agent if not specified
        if not request.target_agent:
            request.target_agent = self._route_task(request)
        
        # Create task result entry
        self._tasks[request.id] = TaskResult(
            task_id=request.id,
            status=TaskStatus.QUEUED,
            agent=request.target_agent or "unknown",
            action=request.action,
        )
        
        # Queue the task
        message = Message(
            id=request.id,
            payload={
                "request": request,
            },
            priority=request.priority,
        )
        await self.message_queue.enqueue(message)
        
        logger.info(
            f"Task {request.id} queued for {request.target_agent}: {request.action}"
        )
        
        return request.id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get the status of a task."""
        return self._tasks.get(task_id)
    
    async def wait_for_task(
        self,
        task_id: str,
        timeout: Optional[int] = None,
    ) -> TaskResult:
        """
        Wait for a task to complete.
        
        Args:
            task_id: The task ID to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            The task result
        """
        timeout = timeout or self.default_timeout
        start_time = datetime.utcnow()
        
        while True:
            result = self._tasks.get(task_id)
            if result and result.status in (
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ):
                return result
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                # Mark as failed due to timeout
                if result:
                    result.status = TaskStatus.FAILED
                    result.error = "Task timed out"
                return result
            
            await asyncio.sleep(0.1)
    
    async def execute_task(self, request: TaskRequest) -> TaskResult:
        """
        Execute a task synchronously (submit and wait).
        
        Args:
            request: The task request
            
        Returns:
            The task result
        """
        task_id = await self.submit_task(request)
        return await self.wait_for_task(task_id, request.timeout_seconds)
    
    def _route_task(self, request: TaskRequest) -> str:
        """
        Determine the appropriate agent for a task.
        
        Uses pattern matching on the action and payload to route
        to the most appropriate specialist agent.
        """
        # Build search text from action and payload
        search_text = f"{request.action} {str(request.payload)}".lower()
        
        # Check routing patterns
        for pattern, agent in self.ROUTING_PATTERNS:
            if re.search(pattern, search_text, re.IGNORECASE):
                # Verify agent is registered
                if self.registry.get(agent):
                    return agent
        
        # Default to root agent
        return "root_agent"
    
    async def _process_queue(self) -> None:
        """Background task to process queued tasks."""
        while not self._shutdown:
            # Check if we can take more tasks
            if len(self._running_tasks) >= self.max_concurrent_tasks:
                await asyncio.sleep(0.1)
                continue
            
            # Try to get next message
            message = await self.message_queue.dequeue()
            if not message:
                await asyncio.sleep(0.1)
                continue
            
            # Process the task
            asyncio.create_task(self._execute_task(message))
    
    async def _execute_task(self, message: Message) -> None:
        """Execute a single task."""
        request: TaskRequest = message.payload["request"]
        task_id = request.id
        
        async with self._lock:
            self._running_tasks.add(task_id)
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.RUNNING
                self._tasks[task_id].started_at = datetime.utcnow()
        
        try:
            # Get the target agent
            agent = self.registry.get(request.target_agent)
            if not agent:
                raise ValueError(f"Agent not found: {request.target_agent}")
            
            # Execute the action
            from agents.specialists import AgentMessage
            
            agent_message = AgentMessage(
                action=request.action,
                payload=request.payload,
            )
            
            response = await asyncio.wait_for(
                agent.process(agent_message),
                timeout=request.timeout_seconds,
            )
            
            # Update task result
            async with self._lock:
                result = self._tasks[task_id]
                result.status = (
                    TaskStatus.COMPLETED if response.success else TaskStatus.FAILED
                )
                result.result = response.result
                result.error = response.error
                result.completed_at = datetime.utcnow()
                result.duration_ms = response.duration_ms
                result.metadata = response.metadata
                
        except asyncio.TimeoutError:
            async with self._lock:
                self._tasks[task_id].status = TaskStatus.FAILED
                self._tasks[task_id].error = "Task execution timed out"
                self._tasks[task_id].completed_at = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            async with self._lock:
                self._tasks[task_id].status = TaskStatus.FAILED
                self._tasks[task_id].error = str(e)
                self._tasks[task_id].completed_at = datetime.utcnow()
        
        finally:
            async with self._lock:
                self._running_tasks.discard(task_id)
    
    async def execute_workflow(
        self,
        workflow: list[TaskRequest],
        parallel: bool = False,
    ) -> list[TaskResult]:
        """
        Execute a multi-step workflow.
        
        Args:
            workflow: List of task requests to execute
            parallel: Whether to execute tasks in parallel
            
        Returns:
            List of task results
        """
        if parallel:
            # Execute all tasks concurrently
            tasks = [self.execute_task(req) for req in workflow]
            return await asyncio.gather(*tasks)
        else:
            # Execute tasks sequentially
            results = []
            for request in workflow:
                result = await self.execute_task(request)
                results.append(result)
                
                # Stop on failure
                if result.status == TaskStatus.FAILED:
                    logger.warning(
                        f"Workflow stopped due to task failure: {request.id}"
                    )
                    break
            
            return results
    
    def get_metrics(self) -> dict[str, Any]:
        """Get orchestrator metrics."""
        total_tasks = len(self._tasks)
        completed = sum(
            1 for t in self._tasks.values()
            if t.status == TaskStatus.COMPLETED
        )
        failed = sum(
            1 for t in self._tasks.values()
            if t.status == TaskStatus.FAILED
        )
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "running_tasks": len(self._running_tasks),
            "queued_tasks": self.message_queue.size(),
            "success_rate": completed / max(total_tasks, 1),
            "registered_agents": len(self.registry.list_agents()),
        }
    
    async def health_check(self) -> dict[str, Any]:
        """Perform orchestrator health check."""
        agents_health = {}
        for agent_info in self.registry.list_agents():
            agent = self.registry.get(agent_info["name"])
            if agent and hasattr(agent, "health_check"):
                try:
                    agents_health[agent_info["name"]] = await agent.health_check()
                except Exception as e:
                    agents_health[agent_info["name"]] = {"status": "error", "error": str(e)}
        
        return {
            "status": "healthy" if not self._shutdown else "stopping",
            "metrics": self.get_metrics(),
            "agents": agents_health,
        }
