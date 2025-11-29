"""
Task Deduplication

Prevents duplicate task execution by tracking task signatures.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TaskSignature:
    """Represents a task signature for deduplication."""
    hash: str
    action: str
    agent: str
    payload_hash: str
    created_at: datetime
    task_id: Optional[str] = None
    status: str = "pending"


class TaskDeduplicator:
    """
    Prevents duplicate task execution.
    
    Features:
    - Hash-based deduplication
    - Configurable TTL
    - Similarity detection
    - Deduplication statistics
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._signatures: dict[str, TaskSignature] = {}
        self._task_to_signature: dict[str, str] = {}
        self._stats = {
            "total_checks": 0,
            "duplicates_found": 0,
            "signatures_created": 0,
        }
    
    def create_signature(
        self,
        action: str,
        agent: Optional[str],
        payload: dict[str, Any],
    ) -> str:
        """
        Create a signature for a task.
        
        Args:
            action: Task action
            agent: Target agent
            payload: Task payload
            
        Returns:
            Signature hash
        """
        # Normalize payload (sort keys, remove None values)
        normalized_payload = self._normalize_payload(payload)
        payload_str = json.dumps(normalized_payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:16]
        
        # Create signature
        signature_str = f"{action}:{agent or 'auto'}:{payload_hash}"
        signature_hash = hashlib.sha256(signature_str.encode()).hexdigest()
        
        return signature_hash
    
    def is_duplicate(
        self,
        action: str,
        agent: Optional[str],
        payload: dict[str, Any],
        task_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a task is a duplicate.
        
        Args:
            action: Task action
            agent: Target agent
            payload: Task payload
            task_id: Optional task ID
            
        Returns:
            (is_duplicate, existing_task_id)
        """
        self._stats["total_checks"] += 1
        
        # Clean expired signatures
        self._cleanup_expired()
        
        # Create signature
        signature_hash = self.create_signature(action, agent, payload)
        
        # Check if signature exists
        existing = self._signatures.get(signature_hash)
        
        if existing:
            # Check if existing task is still pending/running
            if existing.status in ["pending", "queued", "running"]:
                self._stats["duplicates_found"] += 1
                logger.info(
                    f"Duplicate task detected: {signature_hash[:8]}... "
                    f"(existing: {existing.task_id})"
                )
                return True, existing.task_id
        
        # Not a duplicate, create new signature
        signature = TaskSignature(
            hash=signature_hash,
            action=action,
            agent=agent or "auto",
            payload_hash=hashlib.sha256(
                json.dumps(self._normalize_payload(payload), sort_keys=True).encode()
            ).hexdigest()[:16],
            created_at=datetime.utcnow(),
            task_id=task_id,
        )
        
        self._signatures[signature_hash] = signature
        if task_id:
            self._task_to_signature[task_id] = signature_hash
        
        self._stats["signatures_created"] += 1
        return False, None
    
    def register_task(
        self,
        task_id: str,
        action: str,
        agent: Optional[str],
        payload: dict[str, Any],
        status: str = "pending",
    ) -> str:
        """
        Register a task with deduplication.
        
        Returns:
            Signature hash
        """
        signature_hash = self.create_signature(action, agent, payload)
        
        signature = TaskSignature(
            hash=signature_hash,
            action=action,
            agent=agent or "auto",
            payload_hash=hashlib.sha256(
                json.dumps(self._normalize_payload(payload), sort_keys=True).encode()
            ).hexdigest()[:16],
            created_at=datetime.utcnow(),
            task_id=task_id,
            status=status,
        )
        
        self._signatures[signature_hash] = signature
        self._task_to_signature[task_id] = signature_hash
        
        return signature_hash
    
    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status in deduplication tracker."""
        signature_hash = self._task_to_signature.get(task_id)
        if signature_hash and signature_hash in self._signatures:
            self._signatures[signature_hash].status = status
    
    def remove_task(self, task_id: str) -> None:
        """Remove task from deduplication tracker."""
        signature_hash = self._task_to_signature.pop(task_id, None)
        if signature_hash:
            self._signatures.pop(signature_hash, None)
    
    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize payload for consistent hashing."""
        normalized = {}
        
        for key, value in payload.items():
            if value is None:
                continue
            
            if isinstance(value, dict):
                normalized[key] = self._normalize_payload(value)
            elif isinstance(value, list):
                normalized[key] = [
                    self._normalize_payload(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized[key] = value
        
        return normalized
    
    def _cleanup_expired(self) -> None:
        """Remove expired signatures."""
        now = datetime.utcnow()
        expired = [
            sig_hash
            for sig_hash, sig in self._signatures.items()
            if (now - sig.created_at).total_seconds() > self.ttl_seconds
        ]
        
        for sig_hash in expired:
            sig = self._signatures.pop(sig_hash, None)
            if sig and sig.task_id:
                self._task_to_signature.pop(sig.task_id, None)
    
    def get_stats(self) -> dict:
        """Get deduplication statistics."""
        return {
            **self._stats,
            "active_signatures": len(self._signatures),
            "duplicate_rate": (
                self._stats["duplicates_found"] / max(self._stats["total_checks"], 1)
            ),
        }
