"""
Workflow API Routes

REST API endpoints for workflow management.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.core.workflow import WorkflowEngine, WorkflowBuilder
from src.core.workflow.dag import DAG

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models

class WorkflowDefinition(BaseModel):
    """Workflow definition model."""
    name: str
    description: Optional[str] = None
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    metadata: Optional[dict] = None


class WorkflowScheduleRequest(BaseModel):
    """Schedule workflow request."""
    cron_expression: str = Field(..., description="Cron expression (e.g., '0 2 * * *')")
    context: Optional[dict] = None
    enabled: bool = True


class WebhookRegisterRequest(BaseModel):
    """Register webhook request."""
    path: str = Field(..., description="Webhook path (e.g., '/webhook/deploy')")
    method: str = "POST"
    secret: Optional[str] = None
    filters: Optional[dict] = None


# Global workflow engine (injected by app)
workflow_engine: Optional[WorkflowEngine] = None


def set_workflow_engine(engine: WorkflowEngine) -> None:
    """Set the workflow engine instance."""
    global workflow_engine
    workflow_engine = engine


# ============================================================================
# Workflow Management
# ============================================================================

@router.post("/workflows", status_code=status.HTTP_201_CREATED)
async def create_workflow(definition: WorkflowDefinition):
    """Create a new workflow."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    try:
        # Build workflow from definition
        dag = DAG.from_dict({
            "name": definition.name,
            "nodes": definition.nodes,
            "edges": definition.edges,
        })
        
        # Validate
        issues = dag.validate()
        if issues:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow: {', '.join(issues)}",
            )
        
        # Register
        workflow_id = workflow_engine.register(dag)
        
        # Save to persistence
        if definition.metadata:
            await workflow_engine.save_workflow(dag, definition.metadata)
        
        return {
            "id": workflow_id,
            "name": definition.name,
            "status": "created",
        }
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/workflows")
async def list_workflows(
    tags: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
):
    """List all workflows."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    # Get from repository
    tag_list = tags.split(",") if tags else None
    workflows = await workflow_engine.repository.list(tag_list, search, limit)
    
    return {
        "workflows": workflows,
        "total": len(workflows),
    }


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow details."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    workflow = workflow_engine.get(workflow_id)
    if not workflow:
        # Try loading from repository
        workflow = await workflow_engine.load_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "definition": workflow.to_dict(),
    }


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    deleted = workflow_engine.delete(workflow_id)
    if not deleted:
        # Try from repository
        deleted = await workflow_engine.repository.delete(workflow_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )
    
    return {"status": "deleted", "id": workflow_id}


# ============================================================================
# Workflow Execution
# ============================================================================

@router.post("/workflows/{workflow_id}/run")
async def run_workflow(
    workflow_id: str,
    context: Optional[dict] = None,
):
    """Execute a workflow."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    result = await workflow_engine.run(workflow_id, context)
    
    # Save execution
    await workflow_engine.repository.save_execution(
        workflow_id,
        {
            "workflow_id": result.workflow_id,
            "status": result.status.value,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "duration_ms": result.duration_ms,
            "nodes_completed": result.nodes_completed,
            "nodes_failed": result.nodes_failed,
            "error": result.error,
        },
    )
    
    return {
        "workflow_id": result.workflow_id,
        "status": result.status.value,
        "duration_ms": result.duration_ms,
        "nodes_completed": result.nodes_completed,
        "nodes_failed": result.nodes_failed,
    }


@router.get("/workflows/{workflow_id}/runs")
async def list_workflow_runs(
    workflow_id: str,
    limit: int = 50,
):
    """List workflow execution history."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    runs = workflow_engine.list_runs(workflow_id=workflow_id, limit=limit)
    return {"runs": runs}


# ============================================================================
# Scheduling
# ============================================================================

@router.post("/workflows/{workflow_id}/schedule")
async def schedule_workflow(
    workflow_id: str,
    schedule: WorkflowScheduleRequest,
):
    """Schedule a workflow."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    schedule_id = workflow_engine.scheduler.schedule(
        workflow_id,
        schedule.cron_expression,
        schedule.context,
        schedule.enabled,
    )
    
    return {
        "schedule_id": schedule_id,
        "workflow_id": workflow_id,
        "cron": schedule.cron_expression,
        "status": "scheduled",
    }


@router.get("/workflows/{workflow_id}/schedules")
async def list_workflow_schedules(workflow_id: str):
    """List schedules for a workflow."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    all_schedules = workflow_engine.scheduler.list_schedules()
    schedules = [s for s in all_schedules if s["workflow_id"] == workflow_id]
    
    return {"schedules": schedules}


@router.delete("/schedules/{schedule_id}")
async def unschedule_workflow(schedule_id: str):
    """Remove a schedule."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    deleted = workflow_engine.scheduler.unschedule(schedule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule not found: {schedule_id}",
        )
    
    return {"status": "deleted", "schedule_id": schedule_id}


# ============================================================================
# Webhooks
# ============================================================================

@router.post("/workflows/{workflow_id}/webhooks")
async def register_webhook(
    workflow_id: str,
    webhook: WebhookRegisterRequest,
):
    """Register a webhook for a workflow."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    webhook_id = workflow_engine.webhooks.register(
        workflow_id,
        webhook.path,
        webhook.method,
        webhook.secret,
        webhook.filters,
    )
    
    return {
        "webhook_id": webhook_id,
        "workflow_id": workflow_id,
        "path": webhook.path,
        "method": webhook.method,
        "url": f"/api/v1/webhooks/{webhook_id}",
    }


@router.get("/workflows/{workflow_id}/webhooks")
async def list_workflow_webhooks(workflow_id: str):
    """List webhooks for a workflow."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    all_webhooks = workflow_engine.webhooks.list_webhooks()
    webhooks = [w for w in all_webhooks if w["workflow_id"] == workflow_id]
    
    return {"webhooks": webhooks}


@router.post("/webhooks/{webhook_id}/trigger")
async def trigger_webhook(
    webhook_id: str,
    data: dict,
):
    """Trigger a workflow via webhook."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    try:
        result = await workflow_engine.webhooks.trigger(webhook_id, data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/webhooks/{webhook_id}")
async def unregister_webhook(webhook_id: str):
    """Unregister a webhook."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    
    deleted = workflow_engine.webhooks.unregister(webhook_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook not found: {webhook_id}",
        )
    
    return {"status": "deleted", "webhook_id": webhook_id}
