"""
Workflow Engine

High-level interface for workflow management.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .dag import DAG, Node, NodeType
from .executor import WorkflowExecutor, ExecutionResult, WorkflowStatus
from .scheduler import WorkflowScheduler
from .webhooks import WebhookManager
from .persistence import WorkflowRepository
from .checkpointing import CheckpointManager

logger = logging.getLogger(__name__)


@dataclass
class WorkflowConfig:
    """Workflow engine configuration."""
    max_concurrent_workflows: int = 10
    default_timeout: int = 3600
    persist_results: bool = True


class WorkflowEngine:
    """
    High-level workflow engine.
    
    Features:
    - Workflow registration and management
    - Execution scheduling
    - Result persistence
    - Workflow templates
    """
    
    def __init__(
        self,
        config: Optional[WorkflowConfig] = None,
        orchestrator=None,
        db_connection=None,
    ):
        self.config = config or WorkflowConfig()
        self.orchestrator = orchestrator
        
        self._workflows: dict[str, DAG] = {}
        self._runs: dict[str, ExecutionResult] = {}
        self._executor = WorkflowExecutor(orchestrator)
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_workflows)
        
        # Enhanced features
        self._scheduler = WorkflowScheduler(self)
        self._webhooks = WebhookManager(self)
        self._repository = WorkflowRepository(db_connection)
        self._checkpoints = CheckpointManager(db_connection)
    
    # ========================================================================
    # Workflow Management
    # ========================================================================
    
    def register(self, dag: DAG) -> str:
        """Register a workflow."""
        self._workflows[dag.id] = dag
        logger.info(f"Registered workflow: {dag.name} ({dag.id})")
        return dag.id
    
    def get(self, workflow_id: str) -> Optional[DAG]:
        """Get a workflow by ID."""
        return self._workflows.get(workflow_id)
    
    def list(self) -> list[dict]:
        """List all workflows."""
        return [
            {
                "id": dag.id,
                "name": dag.name,
                "nodes": len(dag._nodes),
                "edges": len(dag._edges),
            }
            for dag in self._workflows.values()
        ]
    
    def delete(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False
    
    # ========================================================================
    # Execution
    # ========================================================================
    
    async def run(
        self,
        workflow_id: str,
        context: Optional[dict] = None,
    ) -> ExecutionResult:
        """
        Run a workflow.
        
        Args:
            workflow_id: Workflow to run
            context: Initial context data
            
        Returns:
            ExecutionResult
        """
        dag = self._workflows.get(workflow_id)
        if not dag:
            return ExecutionResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                started_at=datetime.utcnow(),
                error=f"Workflow not found: {workflow_id}",
            )
        
        async with self._semaphore:
            result = await self._executor.execute(dag, context)
        
        # Store result
        self._runs[result.workflow_id] = result
        
        return result
    
    async def run_definition(
        self,
        definition: dict,
        context: Optional[dict] = None,
    ) -> ExecutionResult:
        """Run a workflow from definition (without registering)."""
        dag = DAG.from_dict(definition)
        return await self._executor.execute(dag, context)
    
    def get_run(self, run_id: str) -> Optional[ExecutionResult]:
        """Get a workflow run result."""
        return self._runs.get(run_id)
    
    def list_runs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List workflow runs."""
        runs = list(self._runs.values())
        
        if workflow_id:
            runs = [r for r in runs if r.workflow_id == workflow_id]
        
        if status:
            runs = [r for r in runs if r.status == status]
        
        # Sort by started_at descending
        runs = sorted(runs, key=lambda r: r.started_at, reverse=True)
        
        return [
            {
                "workflow_id": r.workflow_id,
                "status": r.status.value,
                "started_at": r.started_at.isoformat(),
                "duration_ms": r.duration_ms,
                "nodes_completed": r.nodes_completed,
                "nodes_failed": r.nodes_failed,
            }
            for r in runs[:limit]
        ]
    
    # ========================================================================
    # Workflow Builder
    # ========================================================================
    
    def create_workflow(self, name: str) -> "WorkflowBuilder":
        """Create a new workflow using builder pattern."""
        return WorkflowBuilder(name, self)
    
    # ========================================================================
    # Enhanced Features
    # ========================================================================
    
    @property
    def scheduler(self) -> WorkflowScheduler:
        """Get workflow scheduler."""
        return self._scheduler
    
    @property
    def webhooks(self) -> WebhookManager:
        """Get webhook manager."""
        return self._webhooks
    
    @property
    def repository(self) -> WorkflowRepository:
        """Get workflow repository."""
        return self._repository
    
    @property
    def checkpoints(self) -> CheckpointManager:
        """Get checkpoint manager."""
        return self._checkpoints
    
    async def initialize(self) -> None:
        """Initialize workflow engine and start services."""
        await self._scheduler.start()
        logger.info("Workflow engine initialized")
    
    async def shutdown(self) -> None:
        """Shutdown workflow engine."""
        await self._scheduler.stop()
        logger.info("Workflow engine shut down")
    
    async def save_workflow(
        self,
        dag: DAG,
        metadata: Optional[dict] = None,
    ) -> str:
        """Save workflow to persistence layer."""
        workflow_dict = dag.to_dict()
        return await self._repository.save(workflow_dict, metadata)
    
    async def load_workflow(self, workflow_id: str) -> Optional[DAG]:
        """Load workflow from persistence layer."""
        workflow_data = await self._repository.load(workflow_id)
        if not workflow_data:
            return None
        
        definition = workflow_data.get("definition", workflow_data)
        return DAG.from_dict(definition)


class WorkflowBuilder:
    """
    Fluent builder for creating workflows.
    
    Usage:
        workflow = engine.create_workflow("my-workflow")
            .add_task("scan", "scan_vulnerabilities", agent="security_agent")
            .add_task("test", "run_tests", agent="testing_agent")
            .connect("scan", "test")
            .build()
    """
    
    def __init__(self, name: str, engine: WorkflowEngine):
        self._dag = DAG(name=name)
        self._engine = engine
        self._nodes: dict[str, str] = {}  # name -> node_id
    
    def add_task(
        self,
        name: str,
        action: str,
        agent: Optional[str] = None,
        payload: Optional[dict] = None,
        timeout: int = 300,
        continue_on_failure: bool = False,
    ) -> "WorkflowBuilder":
        """Add a task node."""
        node = Node(
            name=name,
            type=NodeType.TASK,
            action=action,
            agent=agent,
            payload=payload or {},
            timeout=timeout,
            continue_on_failure=continue_on_failure,
        )
        node_id = self._dag.add_node(node)
        self._nodes[name] = node_id
        return self
    
    def add_condition(
        self,
        name: str,
        condition: str,
    ) -> "WorkflowBuilder":
        """Add a condition node."""
        node = Node(
            name=name,
            type=NodeType.CONDITION,
            condition=condition,
        )
        node_id = self._dag.add_node(node)
        self._nodes[name] = node_id
        return self
    
    def add_wait(
        self,
        name: str,
        seconds: int,
    ) -> "WorkflowBuilder":
        """Add a wait node."""
        node = Node(
            name=name,
            type=NodeType.WAIT,
            payload={"seconds": seconds},
        )
        node_id = self._dag.add_node(node)
        self._nodes[name] = node_id
        return self
    
    def connect(
        self,
        source: str,
        target: str,
        condition: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """Connect two nodes."""
        source_id = self._nodes.get(source)
        target_id = self._nodes.get(target)
        
        if not source_id:
            raise ValueError(f"Source node not found: {source}")
        if not target_id:
            raise ValueError(f"Target node not found: {target}")
        
        self._dag.add_edge(source_id, target_id, condition)
        return self
    
    def build(self) -> DAG:
        """Build and return the workflow."""
        return self._dag
    
    def register(self) -> str:
        """Build and register the workflow."""
        dag = self.build()
        return self._engine.register(dag)
