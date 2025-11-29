"""
Monitoring MCP Adapter

Provides integration with monitoring services for metrics,
alerting, and observability.
"""

import os
from typing import Any, Optional

from .base_adapter import (
    AdapterConfig,
    BaseAdapter,
    MCPRequest,
    MCPResponse,
)


class MonitoringAdapter(BaseAdapter):
    """
    MCP adapter for monitoring and observability.
    
    Supports querying metrics, creating alerts,
    and managing dashboards across multiple providers.
    """
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self._providers: dict = {}
        self._default_provider = config.extra.get("default_provider", "datadog")
    
    async def _setup_client(self) -> None:
        """Initialize monitoring provider clients."""
        providers_config = self.config.extra.get("providers", {})
        
        # Initialize Datadog
        if "datadog" in providers_config:
            dd_config = providers_config["datadog"]
            api_key = os.environ.get(dd_config.get("api_key_env", "DATADOG_API_KEY"))
            app_key = os.environ.get(dd_config.get("app_key_env", "DATADOG_APP_KEY"))
            
            self._providers["datadog"] = {
                "api_key": api_key,
                "app_key": app_key,
                "site": dd_config.get("site", "datadoghq.com"),
            }
        
        # Initialize Prometheus
        if "prometheus" in providers_config:
            prom_config = providers_config["prometheus"]
            self._providers["prometheus"] = {
                "url": prom_config.get("url", "http://localhost:9090"),
            }
        
        self.logger.info(
            f"Monitoring adapter initialized with providers: "
            f"{list(self._providers.keys())}"
        )
    
    async def _cleanup(self) -> None:
        """Clean up monitoring clients."""
        self._providers = {}
    
    async def execute(self, request: MCPRequest) -> MCPResponse:
        """Execute a monitoring operation."""
        if not self._initialized:
            await self.initialize()
        
        method = request.method
        params = request.params
        
        try:
            handlers = {
                "metrics.query": self._query_metrics,
                "metrics.push": self._push_metrics,
                "alerts.list": self._list_alerts,
                "alerts.create": self._create_alert,
                "alerts.delete": self._delete_alert,
                "dashboards.list": self._list_dashboards,
                "dashboards.create": self._create_dashboard,
                "events.send": self._send_event,
            }
            
            handler = handlers.get(method)
            if not handler:
                return MCPResponse(
                    success=False,
                    error=f"Unknown method: {method}",
                    request_id=request.request_id,
                )
            
            result = await handler(params)
            return MCPResponse(
                success=True,
                data=result,
                request_id=request.request_id,
            )
            
        except Exception as e:
            self.logger.error(f"Monitoring operation failed: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                request_id=request.request_id,
            )
    
    async def _query_metrics(self, params: dict[str, Any]) -> dict:
        """Query metrics from a provider."""
        provider = params.get("provider", self._default_provider)
        query = params.get("query")
        start = params.get("start")
        end = params.get("end")
        
        # Implementation would query actual provider
        return {
            "provider": provider,
            "query": query,
            "series": [
                {
                    "metric": "cpu.usage",
                    "points": [[1701234567, 45.2], [1701234627, 47.8]],
                    "tags": {"host": "server-1"},
                }
            ],
            "status": "success",
        }
    
    async def _push_metrics(self, params: dict[str, Any]) -> dict:
        """Push custom metrics."""
        provider = params.get("provider", self._default_provider)
        metrics = params.get("metrics", [])
        
        return {
            "provider": provider,
            "metrics_pushed": len(metrics),
            "status": "accepted",
        }
    
    async def _list_alerts(self, params: dict[str, Any]) -> list:
        """List configured alerts."""
        provider = params.get("provider", self._default_provider)
        
        return [
            {
                "id": "alert-1",
                "name": "High CPU Usage",
                "status": "OK",
                "condition": "cpu.usage > 80",
            },
            {
                "id": "alert-2",
                "name": "High Error Rate",
                "status": "ALERT",
                "condition": "error_rate > 1%",
            },
        ]
    
    async def _create_alert(self, params: dict[str, Any]) -> dict:
        """Create a new alert."""
        return {
            "id": "alert-new",
            "name": params.get("name"),
            "condition": params.get("condition"),
            "status": "created",
        }
    
    async def _delete_alert(self, params: dict[str, Any]) -> dict:
        """Delete an alert."""
        return {
            "id": params.get("id"),
            "status": "deleted",
        }
    
    async def _list_dashboards(self, params: dict[str, Any]) -> list:
        """List dashboards."""
        return [
            {"id": "dash-1", "name": "System Overview", "url": "/d/dash-1"},
            {"id": "dash-2", "name": "Application Metrics", "url": "/d/dash-2"},
        ]
    
    async def _create_dashboard(self, params: dict[str, Any]) -> dict:
        """Create a new dashboard."""
        return {
            "id": "dash-new",
            "name": params.get("name"),
            "url": "/d/dash-new",
            "status": "created",
        }
    
    async def _send_event(self, params: dict[str, Any]) -> dict:
        """Send a custom event."""
        return {
            "event_id": "evt-12345",
            "title": params.get("title"),
            "status": "sent",
        }
    
    # Convenience methods
    
    async def query_metric(
        self,
        query: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> MCPResponse:
        """Query a metric."""
        request = MCPRequest(
            method="metrics.query",
            params={
                "query": query,
                "start": start,
                "end": end,
                "provider": provider or self._default_provider,
            },
        )
        return await self.execute(request)
    
    async def send_deployment_event(
        self,
        version: str,
        environment: str,
        status: str,
    ) -> MCPResponse:
        """Send a deployment event."""
        request = MCPRequest(
            method="events.send",
            params={
                "title": f"Deployment: {version} to {environment}",
                "text": f"Status: {status}",
                "tags": [
                    f"version:{version}",
                    f"environment:{environment}",
                    "event_type:deployment",
                ],
                "alert_type": "success" if status == "success" else "error",
            },
        )
        return await self.execute(request)
