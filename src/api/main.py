"""
FastAPI Application

Main entry point for the DevOps Brain REST API.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.core import Orchestrator, TaskRequest, MessagePriority
from src.api.websocket import websocket_endpoint, manager as ws_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator: Orchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global orchestrator
    
    # Startup
    logger.info("Starting DevOps Brain API...")
    orchestrator = Orchestrator()
    await orchestrator.start()
    
    # Register default agents (in production, load from config)
    await _register_agents(orchestrator)
    
    # Initialize workflow engine
    from src.core.workflow import WorkflowEngine
    workflow_engine = WorkflowEngine(orchestrator=orchestrator)
    await workflow_engine.initialize()
    
    # Set workflow engine in routes
    from src.api.routes import workflows as workflow_routes
    workflow_routes.set_workflow_engine(workflow_engine)
    
    # Store in app state
    app.state.orchestrator = orchestrator
    app.state.workflow_engine = workflow_engine
    
    logger.info("DevOps Brain API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DevOps Brain API...")
    if orchestrator:
        await orchestrator.stop()
    
    # Shutdown workflow engine
    if hasattr(app.state, "workflow_engine"):
        await app.state.workflow_engine.shutdown()
    
    logger.info("DevOps Brain API stopped")


async def _register_agents(orch: Orchestrator) -> None:
    """Register all specialist agents with the orchestrator."""
    from agents.specialists import (
        AgentConfig,
        SecurityAgent,
        TestingAgent,
        DocumentationAgent,
        PerformanceAgent,
        IncidentResponseAgent,
        DatabaseAgent,
        InfrastructureAgent,
    )
    from agents.specialists.cicd_generator_agent import CICDGeneratorAgent
    from agents.specialists.meta_agent import MetaAgent
    
    agents = [
        ("security_agent", SecurityAgent, [
            "vulnerability_scanning", "secrets_detection", "compliance_checking",
        ]),
        ("testing_agent", TestingAgent, [
            "test_generation", "test_execution", "coverage_analysis",
        ]),
        ("documentation_agent", DocumentationAgent, [
            "api_documentation", "readme_generation", "changelog_management",
        ]),
        ("performance_agent", PerformanceAgent, [
            "performance_profiling", "bottleneck_detection", "load_testing",
        ]),
        ("incident_response_agent", IncidentResponseAgent, [
            "incident_triage", "root_cause_analysis", "runbook_execution",
        ]),
        ("database_agent", DatabaseAgent, [
            "schema_design", "migration_generation", "query_optimization",
        ]),
        ("infrastructure_agent", InfrastructureAgent, [
            "terraform_management", "kubernetes_orchestration", "cost_optimization",
        ]),
        ("cicd_generator_agent", CICDGeneratorAgent, [
            "ci_generation", "workflow_optimization", "pipeline_management",
        ]),
        ("meta_agent", MetaAgent, [
            "agent_analysis", "prompt_optimization", "ab_testing", "self_evolution",
        ]),
    ]
    
    for name, agent_class, capabilities in agents:
        try:
            config = AgentConfig(
                name=name,
                agent_type="specialist",
                capabilities=capabilities,
            )
            agent = agent_class(config)
            await agent.initialize()
            orch.register_agent(name, agent, capabilities)
        except Exception as e:
            logger.error(f"Failed to register {name}: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DevOps Brain API",
        description="AI-powered DevOps automation platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    from .routes import agents, tasks, health, design, workflows
    app.include_router(health.router, tags=["Health"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
    app.include_router(design.router, prefix="/api/v1", tags=["Design"])
    app.include_router(workflows.router, prefix="/api/v1", tags=["Workflows"])
    
    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_route(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        await websocket_endpoint(websocket)
    
    return app


# Create the application instance
app = create_app()


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DevOps Brain API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================================
# Request/Response Models
# ============================================================================

class TaskSubmitRequest(BaseModel):
    """Request model for task submission."""
    
    action: str = Field(..., description="Action to perform")
    payload: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    target_agent: str | None = Field(None, description="Target agent (auto-routed if not specified)")
    priority: str = Field("medium", description="Task priority: critical, high, medium, low")
    timeout_seconds: int = Field(300, description="Task timeout in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "scan_vulnerabilities",
                "payload": {"target": "src/"},
                "priority": "high",
            }
        }


class TaskResponse(BaseModel):
    """Response model for task operations."""
    
    task_id: str
    status: str
    agent: str
    action: str
    result: Any | None = None
    error: str | None = None
    duration_ms: int = 0


# ============================================================================
# Quick Task Endpoints (for convenience)
# ============================================================================

@app.post("/api/v1/execute", response_model=TaskResponse)
async def execute_task(request: TaskSubmitRequest):
    """
    Execute a task synchronously.
    
    This endpoint submits a task and waits for completion.
    For long-running tasks, use /api/v1/tasks/submit instead.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    # Map priority string to enum
    priority_map = {
        "critical": MessagePriority.CRITICAL,
        "high": MessagePriority.HIGH,
        "medium": MessagePriority.MEDIUM,
        "low": MessagePriority.LOW,
    }
    priority = priority_map.get(request.priority.lower(), MessagePriority.MEDIUM)
    
    task_request = TaskRequest(
        action=request.action,
        payload=request.payload,
        target_agent=request.target_agent,
        priority=priority,
        timeout_seconds=request.timeout_seconds,
    )
    
    result = await orchestrator.execute_task(task_request)
    
    return TaskResponse(
        task_id=result.task_id,
        status=result.status.value,
        agent=result.agent,
        action=result.action,
        result=result.result,
        error=result.error,
        duration_ms=result.duration_ms,
    )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )
