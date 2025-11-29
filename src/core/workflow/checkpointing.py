"""
Workflow Checkpointing

Adds checkpoint save/restore functionality (inspired by LangGraph but custom implementation).
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class WorkflowCheckpoint:
    """Represents a saved workflow state."""
    
    def __init__(
        self,
        workflow_id: str,
        execution_id: str,
        state: dict,
        node_states: dict,
        context: dict,
    ):
        self.id = str(uuid4())
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.state = state
        self.node_states = node_states
        self.context = context
        self.created_at = datetime.utcnow()
        self.metadata: dict[str, Any] = {}


class CheckpointManager:
    """
    Manages workflow checkpoints for save/restore functionality.
    
    This provides LangGraph-like checkpointing but optimized for our workflow system.
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self._checkpoints: dict[str, WorkflowCheckpoint] = {}
        self._execution_checkpoints: dict[str, list[str]] = {}  # execution_id -> checkpoint_ids
    
    async def save(
        self,
        workflow_id: str,
        execution_id: str,
        state: dict,
        node_states: dict,
        context: dict,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Save a workflow checkpoint.
        
        Args:
            workflow_id: Workflow ID
            execution_id: Current execution ID
            state: Workflow state
            node_states: Individual node states
            context: Execution context
            metadata: Optional metadata
            
        Returns:
            Checkpoint ID
        """
        checkpoint = WorkflowCheckpoint(
            workflow_id=workflow_id,
            execution_id=execution_id,
            state=state,
            node_states=node_states,
            context=context,
        )
        
        if metadata:
            checkpoint.metadata = metadata
        
        # Store checkpoint
        if self.db:
            await self._save_to_db(checkpoint)
        else:
            self._checkpoints[checkpoint.id] = checkpoint
        
        # Track by execution
        if execution_id not in self._execution_checkpoints:
            self._execution_checkpoints[execution_id] = []
        self._execution_checkpoints[execution_id].append(checkpoint.id)
        
        logger.info(f"Saved checkpoint {checkpoint.id} for workflow {workflow_id}")
        return checkpoint.id
    
    async def load(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """Load a checkpoint by ID."""
        if self.db:
            return await self._load_from_db(checkpoint_id)
        else:
            return self._checkpoints.get(checkpoint_id)
    
    async def get_latest(
        self,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
    ) -> Optional[WorkflowCheckpoint]:
        """Get the latest checkpoint for a workflow or execution."""
        if execution_id:
            checkpoint_ids = self._execution_checkpoints.get(execution_id, [])
            if checkpoint_ids:
                latest_id = checkpoint_ids[-1]
                return await self.load(latest_id)
        
        if workflow_id:
            # Find latest checkpoint for workflow
            checkpoints = [
                cp for cp in self._checkpoints.values()
                if cp.workflow_id == workflow_id
            ]
            if checkpoints:
                return max(checkpoints, key=lambda cp: cp.created_at)
        
        return None
    
    async def list_checkpoints(
        self,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List checkpoints with optional filtering."""
        checkpoints = list(self._checkpoints.values())
        
        if workflow_id:
            checkpoints = [cp for cp in checkpoints if cp.workflow_id == workflow_id]
        
        if execution_id:
            checkpoint_ids = self._execution_checkpoints.get(execution_id, [])
            checkpoints = [cp for cp in checkpoints if cp.id in checkpoint_ids]
        
        # Sort by created_at descending
        checkpoints = sorted(checkpoints, key=lambda cp: cp.created_at, reverse=True)
        
        return [
            {
                "id": cp.id,
                "workflow_id": cp.workflow_id,
                "execution_id": cp.execution_id,
                "created_at": cp.created_at.isoformat(),
                "metadata": cp.metadata,
            }
            for cp in checkpoints[:limit]
        ]
    
    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        if checkpoint_id in self._checkpoints:
            checkpoint = self._checkpoints[checkpoint_id]
            
            # Remove from execution tracking
            if checkpoint.execution_id in self._execution_checkpoints:
                self._execution_checkpoints[checkpoint.execution_id].remove(checkpoint_id)
            
            del self._checkpoints[checkpoint_id]
            return True
        
        if self.db:
            return await self._delete_from_db(checkpoint_id)
        
        return False
    
    async def restore(
        self,
        checkpoint_id: str,
        workflow_engine,
    ) -> dict:
        """
        Restore workflow execution from checkpoint.
        
        Returns:
            Restored state and context
        """
        checkpoint = await self.load(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")
        
        logger.info(f"Restoring workflow {checkpoint.workflow_id} from checkpoint {checkpoint_id}")
        
        return {
            "workflow_id": checkpoint.workflow_id,
            "execution_id": checkpoint.execution_id,
            "state": checkpoint.state,
            "node_states": checkpoint.node_states,
            "context": checkpoint.context,
            "metadata": checkpoint.metadata,
        }
    
    # Database methods (to be implemented)
    
    async def _save_to_db(self, checkpoint: WorkflowCheckpoint) -> None:
        """Save checkpoint to database."""
        # TODO: Implement with SQLAlchemy/asyncpg
        logger.debug(f"Would save checkpoint {checkpoint.id} to DB")
    
    async def _load_from_db(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """Load checkpoint from database."""
        # TODO: Implement
        return None
    
    async def _delete_from_db(self, checkpoint_id: str) -> bool:
        """Delete checkpoint from database."""
        # TODO: Implement
        return False
