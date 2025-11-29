"""
Health Check Routes

Endpoints for monitoring application health and readiness.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Any

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    version: str
    components: dict[str, Any] = {}


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    
    ready: bool
    checks: dict[str, bool] = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns the overall health status of the API and its components.
    """
    from src.api.main import orchestrator
    
    components = {}
    
    if orchestrator:
        try:
            orch_health = await orchestrator.health_check()
            components["orchestrator"] = orch_health
        except Exception as e:
            components["orchestrator"] = {"status": "error", "error": str(e)}
    else:
        components["orchestrator"] = {"status": "not_initialized"}
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        components=components,
    )


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe.
    
    Returns 200 if the application is running.
    """
    return {"status": "alive"}


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_probe():
    """
    Kubernetes readiness probe.
    
    Returns 200 if the application is ready to serve traffic.
    """
    from src.api.main import orchestrator
    
    checks = {
        "orchestrator": orchestrator is not None,
    }
    
    ready = all(checks.values())
    
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready",
        )
    
    return ReadinessResponse(ready=ready, checks=checks)


@router.get("/metrics")
async def metrics():
    """
    Metrics endpoint for monitoring.
    
    Returns key metrics about the orchestrator and agents.
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        return {"error": "Orchestrator not initialized"}
    
    return {
        "orchestrator": orchestrator.get_metrics(),
        "queue": orchestrator.message_queue.get_stats(),
    }
