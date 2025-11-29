"""
Additional Workflow Node Types

Includes human-in-the-loop and other advanced node types.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .dag import Node, NodeType, NodeStatus

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Human approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class HumanApprovalNode(Node):
    """
    Node that pauses workflow for human approval.
    
    Inspired by LangGraph's human-in-the-loop pattern but optimized for DevOps.
    """
    
    approval_timeout: int = 3600  # Timeout in seconds
    notification_channels: list[str] = None  # e.g., ["slack", "email"]
    approval_message: str = "Please approve this workflow step"
    require_reason: bool = False  # Require reason for approval/rejection
    
    def __post_init__(self):
        if self.type != NodeType.TASK:
            self.type = NodeType.TASK
        if not self.notification_channels:
            self.notification_channels = ["slack"]
    
    async def wait_for_approval(
        self,
        notification_service=None,
    ) -> ApprovalStatus:
        """
        Wait for human approval.
        
        Args:
            notification_service: Service to send notifications
            
        Returns:
            ApprovalStatus
        """
        # Send notification
        if notification_service:
            await notification_service.send_approval_request(
                workflow_id=self.id,
                message=self.approval_message,
                channels=self.notification_channels,
                timeout=self.approval_timeout,
            )
        
        # Wait for approval (in real implementation, would poll database/API)
        # For now, simulate with timeout
        try:
            await asyncio.wait_for(
                self._poll_approval(),
                timeout=self.approval_timeout,
            )
            return ApprovalStatus.APPROVED
        except asyncio.TimeoutError:
            logger.warning(f"Approval timeout for node {self.id}")
            return ApprovalStatus.TIMEOUT
    
    async def _poll_approval(self) -> None:
        """Poll for approval status (would check database/API in real implementation)."""
        # In real implementation, would check database for approval status
        # For now, simulate approval after 5 seconds
        await asyncio.sleep(5)
        # In production: await self._check_approval_status()


@dataclass
class ConditionalApprovalNode(Node):
    """
    Conditional approval - only requires approval if condition is met.
    """
    
    condition: str  # Python expression
    approval_node: HumanApprovalNode
    
    async def evaluate_and_approve(self, context: dict) -> bool:
        """Evaluate condition and request approval if needed."""
        # Evaluate condition
        condition_result = eval(self.condition, {"ctx": context})
        
        if condition_result:
            # Condition met, require approval
            status = await self.approval_node.wait_for_approval()
            return status == ApprovalStatus.APPROVED
        
        # Condition not met, auto-approve
        return True


@dataclass
class CheckpointNode(Node):
    """
    Node that saves a checkpoint of workflow state.
    """
    
    checkpoint_name: Optional[str] = None
    checkpoint_manager = None  # Injected at runtime
    
    async def save_checkpoint(self, workflow_state: dict, context: dict) -> str:
        """Save checkpoint."""
        if not self.checkpoint_manager:
            raise ValueError("Checkpoint manager not set")
        
        checkpoint_id = await self.checkpoint_manager.save(
            workflow_id=workflow_state.get("workflow_id"),
            execution_id=workflow_state.get("execution_id"),
            state=workflow_state,
            node_states={},
            context=context,
            metadata={"checkpoint_name": self.checkpoint_name},
        )
        
        logger.info(f"Saved checkpoint {checkpoint_id} at node {self.id}")
        return checkpoint_id


@dataclass
class RetryNode(Node):
    """
    Node with enhanced retry logic.
    """
    
    max_retries: int = 3
    retry_delay: int = 5
    exponential_backoff: bool = True
    retry_on_errors: list[str] = None  # Specific errors to retry on
    
    def __post_init__(self):
        if not self.retry_on_errors:
            self.retry_on_errors = ["timeout", "network_error"]
    
    async def execute_with_retry(self, task_fn) -> Any:
        """Execute task with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await task_fn()
            except Exception as e:
                last_error = e
                error_type = type(e).__name__.lower()
                
                # Check if error is retryable
                if self.retry_on_errors and not any(
                    retryable in error_type for retryable in self.retry_on_errors
                ):
                    raise
                
                if attempt < self.max_retries:
                    delay = self.retry_delay
                    if self.exponential_backoff:
                        delay = self.retry_delay * (2 ** attempt)
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} after {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise last_error
        
        raise last_error
