"""
Agent Orchestrator

Central coordination layer that routes tasks to appropriate specialist agents,
manages agent lifecycle, and handles inter-agent communication.

Enhanced with:
- Circuit breakers for fault tolerance
- Task deduplication
- Load balancing
- Distributed tracing
- Enhanced metrics
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
from .observability.tracing import get_tracer
from .observability.metrics import get_metrics

logger = logging.getLogger(__name__)

# Import enhanced features (with fallback if not available)
try:
    from .orchestrator.circuit_breaker import CircuitBreakerManager, CircuitBreaker
    from .orchestrator.task_deduplication import TaskDeduplicator
    from .orchestrator.load_balancer import LoadBalancer, LoadBalancingStrategy
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False
    logger.warning("Enhanced orchestrator features not available")


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
        enable_deduplication: bool = True,
        enable_load_balancing: bool = True,
        enable_circuit_breaker: bool = True,
    ):
        self.registry = AgentRegistry()
        self.message_queue = MessageQueue()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = default_timeout
        
        self._tasks: dict[str, TaskResult] = {}
        self._running_tasks: set[str] = set()
        self._cancelled_tasks: set[str] = set()
        self._lock = asyncio.Lock()
        self._shutdown = False
        
        # Enhanced features
        if ENHANCED_FEATURES_AVAILABLE:
            self._deduplicator = TaskDeduplicator() if enable_deduplication else None
            self._load_balancer = LoadBalancer() if enable_load_balancing else None
            self._circuit_breakers = CircuitBreakerManager() if enable_circuit_breaker else None
        else:
            self._deduplicator = None
            self._load_balancer = None
            self._circuit_breakers = None
        
        # Observability
        self._tracer = get_tracer("orchestrator")
        self._metrics = get_metrics()
        
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
        with self._tracer.span("orchestrator.submit_task", {
            "task_id": request.id,
            "action": request.action,
        }):
            # Check for duplicates
            if self._deduplicator:
                is_dup, existing_id = self._deduplicator.is_duplicate(
                    request.action,
                    request.target_agent,
                    request.payload,
                )
                if is_dup:
                    logger.info(f"Duplicate task detected, returning existing: {existing_id}")
                    return existing_id
            
            # Determine target agent if not specified
            if not request.target_agent:
                request.target_agent = self._route_task(request)
            
            # Load balancing (if enabled)
            if self._load_balancer and request.target_agent:
                instance_id = await self._load_balancer.select_instance(request.target_agent)
                if instance_id:
                    request.metadata["instance_id"] = instance_id
            
            # Create task result entry
            self._tasks[request.id] = TaskResult(
                task_id=request.id,
                status=TaskStatus.QUEUED,
                agent=request.target_agent or "unknown",
                action=request.action,
            )
            
            # Register with deduplicator
            if self._deduplicator:
                self._deduplicator.register_task(
                    request.id,
                    request.action,
                    request.target_agent,
                    request.payload,
                    "queued",
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
            
            # Record metrics
            self._metrics.increment_counter(
                "tasks_submitted",
                labels={"agent": request.target_agent or "auto", "action": request.action},
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
        
        # Check if cancelled
        if task_id in self._cancelled_tasks:
            async with self._lock:
                self._tasks[task_id].status = TaskStatus.CANCELLED
                self._tasks[task_id].error = "Task was cancelled"
                self._tasks[task_id].completed_at = datetime.utcnow()
                self._cancelled_tasks.discard(task_id)
            return
        
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
            
            # Get circuit breaker
            breaker = None
            if self._circuit_breakers:
                breaker = self._circuit_breakers.get_breaker(request.target_agent)
            
            # Execute with circuit breaker
            from agents.specialists import AgentMessage
            
            agent_message = AgentMessage(
                action=request.action,
                payload=request.payload,
            )
            
            async def execute():
                return await agent.process(agent_message)
            
            if breaker:
                response = await breaker.call(execute)
            else:
                response = await asyncio.wait_for(
                    execute(),
                    timeout=request.timeout_seconds,
                )
            
            # Update task result
            async with self._lock:
                if task_id in self._cancelled_tasks:
                    self._tasks[task_id].status = TaskStatus.CANCELLED
                    self._cancelled_tasks.discard(task_id)
                else:
                    result = self._tasks[task_id]
                    result.status = (
                        TaskStatus.COMPLETED if response.success else TaskStatus.FAILED
                    )
                    result.result = response.result
                    result.error = response.error
                    result.completed_at = datetime.utcnow()
                    result.duration_ms = response.duration_ms
                    result.metadata = response.metadata
                
                # Update deduplicator
                if self._deduplicator:
                    status = "completed" if response.success else "failed"
                    self._deduplicator.update_task_status(task_id, status)
                
                # Release load balancer
                if self._load_balancer and request.target_agent:
                    instance_id = request.metadata.get("instance_id")
                    if instance_id:
                        await self._load_balancer.release_instance(
                            request.target_agent,
                            instance_id,
                        )
                
        except Exception as e:
            error_msg = str(e)
            
            # Check if it's a circuit breaker error
            if "CircuitBreakerOpenError" in str(type(e)):
                error_msg = f"Agent {request.target_agent} circuit breaker is open"
            
            logger.error(f"Task {task_id} failed: {error_msg}")
            async with self._lock:
                if task_id not in self._cancelled_tasks:
                    self._tasks[task_id].status = TaskStatus.FAILED
                    self._tasks[task_id].error = error_msg
                    self._tasks[task_id].completed_at = datetime.utcnow()
                    
                    if self._deduplicator:
                        self._deduplicator.update_task_status(task_id, "failed")
        
        finally:
            async with self._lock:
                self._running_tasks.discard(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if task was cancelled, False if not found or already completed
        """
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            result = self._tasks[task_id]
            
            if result.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return False
            
            # Mark as cancelled
            self._cancelled_tasks.add(task_id)
            result.status = TaskStatus.CANCELLED
            result.error = "Task was cancelled by user"
            result.completed_at = datetime.utcnow()
            
            logger.info(f"Task {task_id} cancelled")
            return True
    
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
        cancelled = sum(
            1 for t in self._tasks.values()
            if t.status == TaskStatus.CANCELLED
        )
        
        metrics = {
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "cancelled_tasks": cancelled,
            "running_tasks": len(self._running_tasks),
            "queued_tasks": self.message_queue.size(),
            "success_rate": completed / max(total_tasks, 1),
            "registered_agents": len(self.registry.list_agents()),
        }
        
        # Add enhanced feature metrics
        if self._deduplicator:
            metrics["deduplication"] = self._deduplicator.get_stats()
        
        if self._load_balancer:
            metrics["load_balancer"] = self._load_balancer.get_stats()
        
        if self._circuit_breakers:
            metrics["circuit_breakers"] = self._circuit_breakers.list_breakers()
        
        return metrics
    
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
