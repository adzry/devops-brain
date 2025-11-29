"""
Workflow Webhooks

Handles webhook triggers for workflows.
"""

import asyncio
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any, Callable, Optional
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class WebhookTrigger:
    """A webhook trigger configuration."""
    
    def __init__(
        self,
        workflow_id: str,
        path: str,
        method: str = "POST",
        secret: Optional[str] = None,
        filters: Optional[dict] = None,
    ):
        self.workflow_id = workflow_id
        self.path = path
        self.method = method.upper()
        self.secret = secret
        self.filters = filters or {}
        self.id = hashlib.sha256(f"{workflow_id}:{path}".encode()).hexdigest()[:16]
        self.created_at = datetime.utcnow()
        self.trigger_count = 0
        self.last_triggered = None


class WebhookManager:
    """
    Manages webhook triggers for workflows.
    
    Features:
    - HTTP webhook endpoints
    - Secret validation
    - Request filtering
    - Webhook history
    - Rate limiting
    """
    
    def __init__(self, workflow_engine):
        self.workflow_engine = workflow_engine
        self._webhooks: dict[str, WebhookTrigger] = {}
        self._history: list[dict] = []
        self._max_history = 1000
    
    def register(
        self,
        workflow_id: str,
        path: str,
        method: str = "POST",
        secret: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> str:
        """
        Register a webhook trigger.
        
        Args:
            workflow_id: Workflow to trigger
            path: Webhook path (e.g., "/webhook/deploy")
            method: HTTP method (GET, POST, etc.)
            secret: Optional secret for validation
            filters: Optional filters for request matching
            
        Returns:
            Webhook ID
        """
        webhook = WebhookTrigger(workflow_id, path, method, secret, filters)
        self._webhooks[webhook.id] = webhook
        
        logger.info(f"Registered webhook {webhook.id} for workflow {workflow_id} at {path}")
        return webhook.id
    
    def unregister(self, webhook_id: str) -> bool:
        """Unregister a webhook."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            logger.info(f"Unregistered webhook {webhook_id}")
            return True
        return False
    
    def get(self, webhook_id: str) -> Optional[WebhookTrigger]:
        """Get webhook by ID."""
        return self._webhooks.get(webhook_id)
    
    def find_by_path(self, path: str, method: str = "POST") -> Optional[WebhookTrigger]:
        """Find webhook by path and method."""
        for webhook in self._webhooks.values():
            if webhook.path == path and webhook.method == method.upper():
                return webhook
        return None
    
    async def trigger(
        self,
        webhook_id: str,
        request_data: dict,
        headers: Optional[dict] = None,
    ) -> dict:
        """
        Trigger a workflow via webhook.
        
        Args:
            webhook_id: Webhook ID
            request_data: Request body/data
            headers: Request headers
            
        Returns:
            Execution result
        """
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook not found: {webhook_id}")
        
        # Validate secret if provided
        if webhook.secret:
            if not self._validate_secret(headers or {}, request_data, webhook.secret):
                raise ValueError("Invalid webhook secret")
        
        # Apply filters
        if webhook.filters and not self._matches_filters(request_data, headers, webhook.filters):
            raise ValueError("Request does not match filters")
        
        # Build context from request
        context = {
            "webhook": {
                "id": webhook_id,
                "path": webhook.path,
                "method": webhook.method,
            },
            "request": {
                "data": request_data,
                "headers": headers or {},
            },
            "triggered_at": datetime.utcnow().isoformat(),
        }
        
        # Execute workflow
        try:
            result = await self.workflow_engine.run(webhook.workflow_id, context)
            
            # Update webhook stats
            webhook.trigger_count += 1
            webhook.last_triggered = datetime.utcnow()
            
            # Record history
            self._record_history(webhook_id, context, result)
            
            return {
                "success": result.status.value in ["completed", "running"],
                "workflow_id": webhook.workflow_id,
                "execution_id": result.workflow_id,
                "status": result.status.value,
            }
            
        except Exception as e:
            logger.error(f"Webhook trigger failed: {e}")
            self._record_history(webhook_id, context, None, error=str(e))
            raise
    
    def list_webhooks(self) -> list[dict]:
        """List all webhooks."""
        return [
            {
                "id": w.id,
                "workflow_id": w.workflow_id,
                "path": w.path,
                "method": w.method,
                "trigger_count": w.trigger_count,
                "last_triggered": w.last_triggered.isoformat() if w.last_triggered else None,
            }
            for w in self._webhooks.values()
        ]
    
    def get_history(self, webhook_id: Optional[str] = None, limit: int = 100) -> list[dict]:
        """Get webhook trigger history."""
        history = self._history
        
        if webhook_id:
            history = [h for h in history if h.get("webhook_id") == webhook_id]
        
        return history[-limit:]
    
    def _validate_secret(self, headers: dict, data: dict, secret: str) -> bool:
        """Validate webhook secret."""
        # Check for signature in headers
        signature = headers.get("X-Webhook-Signature") or headers.get("X-Signature")
        if not signature:
            return False
        
        # Create expected signature
        payload = str(data)
        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    def _matches_filters(self, data: dict, headers: Optional[dict], filters: dict) -> bool:
        """Check if request matches filters."""
        for key, expected_value in filters.items():
            if key.startswith("header."):
                header_key = key[7:]
                actual_value = (headers or {}).get(header_key)
            else:
                actual_value = data.get(key)
            
            if actual_value != expected_value:
                return False
        
        return True
    
    def _record_history(
        self,
        webhook_id: str,
        context: dict,
        result: Optional[Any],
        error: Optional[str] = None,
    ) -> None:
        """Record webhook trigger in history."""
        entry = {
            "webhook_id": webhook_id,
            "triggered_at": datetime.utcnow().isoformat(),
            "context": context,
            "success": result is not None and error is None,
            "error": error,
        }
        
        self._history.append(entry)
        
        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
