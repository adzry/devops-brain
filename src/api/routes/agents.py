"""
Agent Routes

Endpoints for managing and interacting with agents.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any

router = APIRouter()


class AgentInfo(BaseModel):
    """Agent information model."""
    
    name: str
    status: str
    capabilities: list[str]
    metrics: dict[str, Any] | None = None


class AgentListResponse(BaseModel):
    """Response for listing agents."""
    
    agents: list[AgentInfo]
    total: int


class AgentActionRequest(BaseModel):
    """Request for executing an agent action."""
    
    action: str = Field(..., description="Action to execute")
    payload: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "scan_vulnerabilities",
                "payload": {"target": "src/", "scan_type": "full"},
            }
        }


class AgentActionResponse(BaseModel):
    """Response from agent action execution."""
    
    success: bool
    agent: str
    action: str
    result: Any | None = None
    error: str | None = None
    duration_ms: int = 0
    recommendations: list[str] = []


@router.get("", response_model=AgentListResponse)
async def list_agents():
    """
    List all registered agents.
    
    Returns information about all agents including their capabilities and status.
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    agents = orchestrator.registry.list_agents()
    
    agent_infos = []
    for agent in agents:
        agent_instance = orchestrator.registry.get(agent["name"])
        metrics = None
        if agent_instance and hasattr(agent_instance, "get_metrics"):
            metrics = agent_instance.get_metrics()
        
        agent_infos.append(AgentInfo(
            name=agent["name"],
            status=agent["status"],
            capabilities=agent["capabilities"],
            metrics=metrics,
        ))
    
    return AgentListResponse(agents=agent_infos, total=len(agent_infos))


@router.get("/{agent_name}", response_model=AgentInfo)
async def get_agent(agent_name: str):
    """
    Get information about a specific agent.
    
    Args:
        agent_name: Name of the agent
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    agent = orchestrator.registry.get(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}",
        )
    
    # Get agent info from registry
    agents = orchestrator.registry.list_agents()
    agent_info = next((a for a in agents if a["name"] == agent_name), None)
    
    metrics = None
    if hasattr(agent, "get_metrics"):
        metrics = agent.get_metrics()
    
    return AgentInfo(
        name=agent_name,
        status=agent_info["status"] if agent_info else "unknown",
        capabilities=agent_info["capabilities"] if agent_info else [],
        metrics=metrics,
    )


@router.post("/{agent_name}/execute", response_model=AgentActionResponse)
async def execute_agent_action(agent_name: str, request: AgentActionRequest):
    """
    Execute an action on a specific agent.
    
    Args:
        agent_name: Name of the agent
        request: Action request with action name and payload
    """
    from src.api.main import orchestrator
    from agents.specialists import AgentMessage
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    agent = orchestrator.registry.get(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}",
        )
    
    try:
        message = AgentMessage(
            action=request.action,
            payload=request.payload,
        )
        
        response = await agent.process(message)
        
        return AgentActionResponse(
            success=response.success,
            agent=agent_name,
            action=request.action,
            result=response.result,
            error=response.error,
            duration_ms=response.duration_ms,
            recommendations=response.recommendations,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action execution failed: {str(e)}",
        )


@router.get("/{agent_name}/health")
async def get_agent_health(agent_name: str):
    """
    Get health status of a specific agent.
    
    Args:
        agent_name: Name of the agent
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    agent = orchestrator.registry.get(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}",
        )
    
    if hasattr(agent, "health_check"):
        return await agent.health_check()
    
    return {"status": "unknown", "message": "Agent does not support health checks"}


@router.get("/{agent_name}/capabilities")
async def get_agent_capabilities(agent_name: str):
    """
    Get capabilities of a specific agent.
    
    Args:
        agent_name: Name of the agent
    """
    from src.api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    agents = orchestrator.registry.list_agents()
    agent_info = next((a for a in agents if a["name"] == agent_name), None)
    
    if not agent_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}",
        )
    
    return {
        "agent": agent_name,
        "capabilities": agent_info["capabilities"],
    }
