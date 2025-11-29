"""
Base Agent Implementation

Provides the foundation for all specialist agents with common functionality
for task execution, inter-agent communication, and result handling.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class AgentStatus(Enum):
    """Agent operational status."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""
    
    name: str
    agent_type: str
    model: str = "gpt-5.1-codex-high"
    capabilities: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    system_prompt: Optional[str] = None
    max_retries: int = 3
    timeout_seconds: int = 300


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = ""
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None


@dataclass
class AgentResponse:
    """Response structure from agent task execution."""
    
    success: bool
    message_id: str
    agent_name: str
    action: str
    result: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Abstract base class for all specialist agents.
    
    Provides common functionality for:
    - Task queue management
    - Inter-agent messaging
    - Error handling and retries
    - Metrics and logging
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(f"agent.{config.name}")
        self._status = AgentStatus.IDLE
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._handlers: dict[str, Callable] = {}
        self._metrics: dict[str, int] = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_duration_ms": 0,
        }
        self._register_handlers()
    
    @property
    def name(self) -> str:
        """Agent name."""
        return self.config.name
    
    @property
    def status(self) -> AgentStatus:
        """Current agent status."""
        return self._status
    
    @property
    def capabilities(self) -> list[str]:
        """List of agent capabilities."""
        return self.config.capabilities
    
    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.config.capabilities
    
    @abstractmethod
    def _register_handlers(self) -> None:
        """Register action handlers. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    def register_handler(self, action: str, handler: Callable) -> None:
        """Register a handler for a specific action."""
        self._handlers[action] = handler
        self.logger.debug(f"Registered handler for action: {action}")
    
    async def process(self, message: AgentMessage) -> AgentResponse:
        """
        Process an incoming message and execute the requested action.
        
        Args:
            message: The incoming agent message
            
        Returns:
            AgentResponse with the result of the action
        """
        start_time = datetime.utcnow()
        self._status = AgentStatus.BUSY
        
        self.logger.info(
            f"Processing message {message.id}: action={message.action}"
        )
        
        try:
            handler = self._handlers.get(message.action)
            if not handler:
                return AgentResponse(
                    success=False,
                    message_id=message.id,
                    agent_name=self.name,
                    action=message.action,
                    error=f"Unknown action: {message.action}",
                )
            
            result = await self._execute_with_retry(handler, message.payload)
            
            duration = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            self._metrics["tasks_completed"] += 1
            self._metrics["total_duration_ms"] += duration
            
            return AgentResponse(
                success=True,
                message_id=message.id,
                agent_name=self.name,
                action=message.action,
                result=result.get("data"),
                duration_ms=duration,
                metadata=result.get("metadata", {}),
                recommendations=result.get("recommendations", []),
                next_actions=result.get("next_actions", []),
            )
            
        except Exception as e:
            self.logger.error(f"Action failed: {message.action} - {e}")
            self._metrics["tasks_failed"] += 1
            
            return AgentResponse(
                success=False,
                message_id=message.id,
                agent_name=self.name,
                action=message.action,
                error=str(e),
                duration_ms=int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
            )
        finally:
            self._status = AgentStatus.IDLE
    
    async def _execute_with_retry(
        self,
        handler: Callable,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a handler with retry logic."""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                return await handler(payload)
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(
                        f"Retry {attempt + 1}/{self.config.max_retries} "
                        f"in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
        
        raise last_error
    
    async def send_message(
        self,
        recipient: str,
        action: str,
        payload: dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> AgentMessage:
        """
        Create and send a message to another agent.
        
        Args:
            recipient: Target agent name
            action: Action to perform
            payload: Action parameters
            priority: Message priority
            
        Returns:
            The created message
        """
        message = AgentMessage(
            sender=self.name,
            recipient=recipient,
            action=action,
            payload=payload,
            priority=priority,
        )
        
        # In production, this would publish to a message queue
        self.logger.info(
            f"Sending message to {recipient}: action={action}"
        )
        
        return message
    
    async def delegate_task(
        self,
        agent_name: str,
        task: str,
        context: dict[str, Any],
    ) -> AgentResponse:
        """
        Delegate a task to another specialist agent.
        
        Args:
            agent_name: Name of the target agent
            task: Task description
            context: Task context and parameters
            
        Returns:
            Response from the delegated agent
        """
        self.logger.info(f"Delegating task to {agent_name}: {task}")
        
        # In production, this would route through the orchestrator
        return AgentResponse(
            success=True,
            message_id=str(uuid.uuid4()),
            agent_name=agent_name,
            action="delegated_task",
            result={"delegated": True, "task": task},
        )
    
    def get_metrics(self) -> dict[str, Any]:
        """Get agent performance metrics."""
        avg_duration = 0
        if self._metrics["tasks_completed"] > 0:
            avg_duration = (
                self._metrics["total_duration_ms"]
                / self._metrics["tasks_completed"]
            )
        
        return {
            "agent_name": self.name,
            "status": self._status.value,
            "tasks_completed": self._metrics["tasks_completed"],
            "tasks_failed": self._metrics["tasks_failed"],
            "success_rate": (
                self._metrics["tasks_completed"]
                / max(
                    self._metrics["tasks_completed"]
                    + self._metrics["tasks_failed"],
                    1,
                )
            ),
            "average_duration_ms": avg_duration,
        }
    
    async def health_check(self) -> dict[str, Any]:
        """Perform a health check on the agent."""
        return {
            "agent": self.name,
            "status": "healthy" if self._status != AgentStatus.ERROR else "unhealthy",
            "capabilities": len(self.capabilities),
            "metrics": self.get_metrics(),
        }
