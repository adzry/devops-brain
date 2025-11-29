"""
Task Routes

Endpoints for task management and execution.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any

from src.core import TaskRequest, MessagePriority

router = APIRouter()


class TaskSubmitRequest(BaseModel):
    """Request model for task submission."""
    
    action: str = Field(..., description="Action to perform")
    payload: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    target_agent: str | None = Field(None, description="Target agent (auto-routed if not specified)")
    priority: str = Field("medium", description="Task priority: critical, high, medium, low")
    timeout_seconds: int = Field(300, description="Task timeout in seconds", ge=1, le=3600)
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "scan_vulnerabilities",
                "payload": {"target": "src/"},
                "target_agent": "security_agent",
                "priority": "high",
                "timeout_seconds": 300,
            }
        }


class TaskSubmitResponse(BaseModel):
    """Response for task submission."""
    
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response for task status."""
    
    task_id: str
    status: str
    agent: str
    action: str
    result: Any | None = None
    error: str | None = None
    duration_ms: int = 0
    started_at: str | None = None
    completed_at: str | None = None


class TaskExecuteResponse(BaseModel):
    """Response for synchronous task execution."""
    
    task_id: str
    status: str
    agent: str
    action: str
    result: Any | None = None
    error: str | None = None
    duration_ms: int = 0


class WorkflowRequest(BaseModel):
    """Request for workflow execution."""
    
    tasks: list[TaskSubmitRequest] = Field(..., description="List of tasks to execute")
    parallel: bool = Field(False, description="Execute tasks in parallel")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [
                    {"action": "scan_vulnerabilities", "payload": {"target": "src/"}},
                    {"action": "generate_tests", "payload": {"file": "src/api.py"}},
                ],
                "parallel": False,
            }
        }


def _get_priority(priority_str: str) -> MessagePriority:
    """Convert priority string to enum."""
    priority_map = {
        "critical": MessagePriority.CRITICAL,
        "high": MessagePriority.HIGH,
        "medium": MessagePriority.MEDIUM,
        "low": MessagePriority.LOW,
    }
    return priority_map.get(priority_str.lower(), MessagePriority.MEDIUM)


@router.post("/submit", response_model=TaskSubmitResponse)
async def submit_task(request: TaskSubmitRequest):
    """
    Submit a task for asynchronous execution.
    
    The task will be queued and processed in the background.
    Use GET /tasks/{task_id} to check status.
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    task_request = TaskRequest(
        action=request.action,
        payload=request.payload,
        target_agent=request.target_agent,
        priority=_get_priority(request.priority),
        timeout_seconds=request.timeout_seconds,
    )
    
    task_id = await orchestrator.submit_task(task_request)
    
    return TaskSubmitResponse(
        task_id=task_id,
        status="queued",
        message=f"Task queued for execution by {task_request.target_agent or 'auto-routed agent'}",
    )


@router.post("/execute", response_model=TaskExecuteResponse)
async def execute_task(request: TaskSubmitRequest):
    """
    Execute a task synchronously.
    
    This endpoint submits a task and waits for completion.
    For long-running tasks, use POST /tasks/submit instead.
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    task_request = TaskRequest(
        action=request.action,
        payload=request.payload,
        target_agent=request.target_agent,
        priority=_get_priority(request.priority),
        timeout_seconds=request.timeout_seconds,
    )
    
    result = await orchestrator.execute_task(task_request)
    
    return TaskExecuteResponse(
        task_id=result.task_id,
        status=result.status.value,
        agent=result.agent,
        action=result.action,
        result=result.result,
        error=result.error,
        duration_ms=result.duration_ms,
    )


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a task.
    
    Args:
        task_id: The task ID returned from submit
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    result = await orchestrator.get_task_status(task_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )
    
    return TaskStatusResponse(
        task_id=result.task_id,
        status=result.status.value,
        agent=result.agent,
        action=result.action,
        result=result.result,
        error=result.error,
        duration_ms=result.duration_ms,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
    )


@router.post("/{task_id}/wait", response_model=TaskStatusResponse)
async def wait_for_task(task_id: str, timeout: int = 300):
    """
    Wait for a task to complete.
    
    Args:
        task_id: The task ID to wait for
        timeout: Maximum time to wait in seconds (default: 300)
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    result = await orchestrator.wait_for_task(task_id, timeout)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )
    
    return TaskStatusResponse(
        task_id=result.task_id,
        status=result.status.value,
        agent=result.agent,
        action=result.action,
        result=result.result,
        error=result.error,
        duration_ms=result.duration_ms,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
    )


@router.post("/workflow")
async def execute_workflow(request: WorkflowRequest):
    """
    Execute a multi-task workflow.
    
    Tasks can be executed sequentially or in parallel.
    Sequential execution stops on first failure.
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    # Convert requests to TaskRequest objects
    task_requests = [
        TaskRequest(
            action=task.action,
            payload=task.payload,
            target_agent=task.target_agent,
            priority=_get_priority(task.priority),
            timeout_seconds=task.timeout_seconds,
        )
        for task in request.tasks
    ]
    
    results = await orchestrator.execute_workflow(task_requests, request.parallel)
    
    return {
        "workflow_id": results[0].task_id if results else None,
        "parallel": request.parallel,
        "total_tasks": len(request.tasks),
        "completed": sum(1 for r in results if r.status.value == "completed"),
        "failed": sum(1 for r in results if r.status.value == "failed"),
        "results": [
            {
                "task_id": r.task_id,
                "status": r.status.value,
                "agent": r.agent,
                "action": r.action,
                "result": r.result,
                "error": r.error,
                "duration_ms": r.duration_ms,
            }
            for r in results
        ],
    }


@router.get("")
async def list_tasks(
    status: str | None = None,
    limit: int = 100,
):
    """
    List recent tasks.
    
    Args:
        status: Filter by status (pending, running, completed, failed)
        limit: Maximum number of tasks to return
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    # Get all tasks (in production, this would query a database)
    all_tasks = list(orchestrator._tasks.values())
    
    # Filter by status if specified
    if status:
        all_tasks = [t for t in all_tasks if t.status.value == status]
    
    # Sort by creation time (most recent first) and limit
    all_tasks = sorted(
        all_tasks,
        key=lambda t: t.started_at or t.completed_at or "",
        reverse=True,
    )[:limit]
    
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "status": t.status.value,
                "agent": t.agent,
                "action": t.action,
                "duration_ms": t.duration_ms,
            }
            for t in all_tasks
        ],
        "total": len(all_tasks),
    }
