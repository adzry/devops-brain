"""
Event Types

Defines event types and structures for the event system.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EventType(Enum):
    """Event categories."""
    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_ERROR = "agent.error"
    AGENT_MESSAGE = "agent.message"
    
    # Task events
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_HEALTH_CHECK = "system.health_check"
    
    # Integration events
    WEBHOOK_RECEIVED = "webhook.received"
    NOTIFICATION_SENT = "notification.sent"


@dataclass
class Event:
    """Base event structure."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.SYSTEM_STARTUP
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    correlation_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


@dataclass
class AgentEvent(Event):
    """Agent-specific event."""
    agent_id: str = ""
    agent_name: str = ""
    action: str = ""
    
    def __post_init__(self):
        self.data.update({
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action": self.action,
        })


@dataclass
class TaskEvent(Event):
    """Task-specific event."""
    task_id: str = ""
    agent_id: str = ""
    status: str = ""
    progress: float = 0.0
    result: Any = None
    error: Optional[str] = None
    
    def __post_init__(self):
        self.data.update({
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
        })


@dataclass
class SystemEvent(Event):
    """System-level event."""
    component: str = ""
    severity: str = "info"  # info, warning, error, critical
    message: str = ""
    
    def __post_init__(self):
        self.data.update({
            "component": self.component,
            "severity": self.severity,
            "message": self.message,
        })
