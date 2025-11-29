"""
Workflow Executor

Executes workflow DAGs with proper dependency handling.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .dag import DAG, Node, NodeStatus, NodeType

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    nodes_completed: int = 0
    nodes_failed: int = 0
    node_results: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class WorkflowExecutor:
    """
    Executes workflow DAGs.
    
    Features:
    - Parallel execution of independent nodes
    - Dependency resolution
    - Error handling and retries
    - Conditional branching
    - Progress tracking
    """
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self._context: dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def execute(
        self,
        dag: DAG,
        initial_context: Optional[dict] = None,
    ) -> ExecutionResult:
        """
        Execute a workflow DAG.
        
        Args:
            dag: The workflow DAG to execute
            initial_context: Initial context data
            
        Returns:
            ExecutionResult with status and results
        """
        # Validate DAG
        issues = dag.validate()
        if issues:
            return ExecutionResult(
                workflow_id=dag.id,
                status=WorkflowStatus.FAILED,
                started_at=datetime.utcnow(),
                error=f"Invalid DAG: {', '.join(issues)}",
            )
        
        # Initialize execution
        started_at = datetime.utcnow()
        self._context = initial_context or {}
        
        result = ExecutionResult(
            workflow_id=dag.id,
            status=WorkflowStatus.RUNNING,
            started_at=started_at,
        )
        
        try:
            # Get execution order
            order = dag.topological_sort()
            logger.info(f"Executing workflow {dag.name} with {len(order)} nodes")
            
            # Track completed nodes
            completed = set()
            
            # Execute nodes
            while len(completed) < len(order):
                # Find ready nodes (all parents completed)
                ready = []
                for node_id in order:
                    if node_id in completed:
                        continue
                    
                    node = dag.get_node(node_id)
                    parents = dag.get_parents(node_id)
                    
                    # Check if all parents are completed
                    if all(p in completed for p in parents):
                        # Check if any parent failed (and not continue_on_failure)
                        parent_failed = any(
                            dag.get_node(p).status == NodeStatus.FAILED
                            for p in parents
                        )
                        
                        if parent_failed and not node.continue_on_failure:
                            node.status = NodeStatus.SKIPPED
                            completed.add(node_id)
                        else:
                            ready.append(node_id)
                
                if not ready:
                    # No progress possible
                    break
                
                # Execute ready nodes in parallel
                tasks = [
                    self._execute_node(dag.get_node(nid), dag)
                    for nid in ready
                ]
                
                await asyncio.gather(*tasks)
                
                # Update completed
                for node_id in ready:
                    completed.add(node_id)
                    node = dag.get_node(node_id)
                    result.node_results[node_id] = {
                        "status": node.status.value,
                        "result": node.result,
                        "error": node.error,
                    }
                    
                    if node.status == NodeStatus.COMPLETED:
                        result.nodes_completed += 1
                    elif node.status == NodeStatus.FAILED:
                        result.nodes_failed += 1
            
            # Determine final status
            if result.nodes_failed > 0:
                result.status = WorkflowStatus.FAILED
            else:
                result.status = WorkflowStatus.COMPLETED
            
        except asyncio.CancelledError:
            result.status = WorkflowStatus.CANCELLED
            result.error = "Workflow cancelled"
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
        
        finally:
            result.completed_at = datetime.utcnow()
            result.duration_ms = int(
                (result.completed_at - result.started_at).total_seconds() * 1000
            )
        
        return result
    
    async def _execute_node(self, node: Node, dag: DAG) -> None:
        """Execute a single node."""
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.utcnow().isoformat()
        
        try:
            logger.debug(f"Executing node {node.name or node.id}")
            
            if node.type == NodeType.TASK:
                await self._execute_task(node)
                
            elif node.type == NodeType.CONDITION:
                await self._execute_condition(node, dag)
                
            elif node.type == NodeType.TRANSFORM:
                await self._execute_transform(node)
                
            elif node.type == NodeType.WAIT:
                await self._execute_wait(node)
                
            elif node.type == NodeType.PARALLEL:
                await self._execute_parallel(node, dag)
            
            node.status = NodeStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Node {node.name} failed: {e}")
            node.status = NodeStatus.FAILED
            node.error = str(e)
            
            # Retry logic
            if node.retry_count > 0:
                for attempt in range(node.retry_count):
                    try:
                        await asyncio.sleep(node.retry_delay)
                        await self._execute_task(node)
                        node.status = NodeStatus.COMPLETED
                        node.error = None
                        break
                    except Exception:
                        continue
        
        finally:
            node.completed_at = datetime.utcnow().isoformat()
    
    async def _execute_task(self, node: Node) -> None:
        """Execute a task node."""
        if self.orchestrator:
            # Use orchestrator
            from src.core.orchestrator import TaskRequest
            
            # Interpolate payload with context
            payload = self._interpolate(node.payload)
            
            request = TaskRequest(
                action=node.action,
                payload=payload,
                target_agent=node.agent,
                timeout_seconds=node.timeout,
            )
            
            result = await self.orchestrator.execute_task(request)
            
            if result.status.value == "failed":
                raise Exception(result.error)
            
            node.result = result.result
            
            # Update context with result
            async with self._lock:
                self._context[node.id] = result.result
        else:
            # Mock execution
            node.result = {"mock": True, "action": node.action}
            async with self._lock:
                self._context[node.id] = node.result
    
    async def _execute_condition(self, node: Node, dag: DAG) -> None:
        """Execute a condition node."""
        # Evaluate condition
        result = False
        
        if node.condition_fn:
            result = node.condition_fn(self._context)
        elif node.condition:
            # Simple expression evaluation (be careful with eval!)
            result = eval(node.condition, {"ctx": self._context})
        
        node.result = {"condition": node.condition, "result": result}
        
        # Mark non-matching branches as skipped
        children = dag.get_children(node.id)
        for child_id in children:
            edge = next(
                (e for e in dag._edges if e.source == node.id and e.target == child_id),
                None,
            )
            
            if edge and edge.condition:
                should_take = (edge.condition == "true" and result) or \
                             (edge.condition == "false" and not result)
                
                if not should_take:
                    child = dag.get_node(child_id)
                    child.status = NodeStatus.SKIPPED
    
    async def _execute_transform(self, node: Node) -> None:
        """Execute a transform node."""
        if node.transform_fn:
            node.result = node.transform_fn(self._context)
            async with self._lock:
                self._context[node.id] = node.result
        else:
            node.result = self._context.copy()
    
    async def _execute_wait(self, node: Node) -> None:
        """Execute a wait node."""
        wait_time = node.payload.get("seconds", 1)
        await asyncio.sleep(wait_time)
        node.result = {"waited_seconds": wait_time}
    
    async def _execute_parallel(self, node: Node, dag: DAG) -> None:
        """Execute parallel branches."""
        children = dag.get_children(node.id)
        
        # Execute all children in parallel
        tasks = [
            self._execute_node(dag.get_node(cid), dag)
            for cid in children
        ]
        
        await asyncio.gather(*tasks)
        
        # Collect results
        node.result = {
            cid: dag.get_node(cid).result
            for cid in children
        }
    
    def _interpolate(self, data: Any) -> Any:
        """Interpolate context variables in data."""
        if isinstance(data, str):
            # Simple interpolation: ${node_id.field}
            import re
            pattern = r'\$\{([^}]+)\}'
            
            def replace(match):
                path = match.group(1).split('.')
                value = self._context
                for key in path:
                    if isinstance(value, dict):
                        value = value.get(key, match.group(0))
                    else:
                        return match.group(0)
                return str(value)
            
            return re.sub(pattern, replace, data)
            
        elif isinstance(data, dict):
            return {k: self._interpolate(v) for k, v in data.items()}
            
        elif isinstance(data, list):
            return [self._interpolate(v) for v in data]
        
        return data
