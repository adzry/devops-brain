"""
Unified MCP Manager

Centralizes all MCP adapters into a single interface, enabling
seamless integration between design tools (Figma) and DevOps tools.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable
import structlog

from .adapters.base_adapter import AdapterConfig, BaseAdapter, MCPRequest, MCPResponse
from .adapters.github_adapter import GitHubAdapter
from .adapters.slack_adapter import SlackAdapter
from .adapters.postgres_adapter import PostgresAdapter
from .adapters.monitoring_adapter import MonitoringAdapter
from .adapters.figma_adapter import FigmaAdapter


logger = structlog.get_logger(__name__)


class AdapterType(str, Enum):
    """Available adapter types."""
    GITHUB = "github"
    SLACK = "slack"
    POSTGRES = "postgres"
    MONITORING = "monitoring"
    FIGMA = "figma"


@dataclass
class MCPConfig:
    """Configuration for the MCP Manager."""
    enabled_adapters: list[AdapterType] = field(default_factory=list)
    default_timeout: float = 30.0
    retry_attempts: int = 3
    cache_enabled: bool = True
    cache_ttl: int = 300
    
    # Adapter-specific configs
    github: dict = field(default_factory=dict)
    slack: dict = field(default_factory=dict)
    postgres: dict = field(default_factory=dict)
    monitoring: dict = field(default_factory=dict)
    figma: dict = field(default_factory=dict)


@dataclass
class UnifiedRequest:
    """Unified request format for all adapters."""
    adapter: AdapterType
    method: str
    params: dict = field(default_factory=dict)
    timeout: Optional[float] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class UnifiedResponse:
    """Unified response format from all adapters."""
    success: bool
    adapter: AdapterType
    data: Any = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class MCPManager:
    """
    Unified MCP Manager that orchestrates all adapters.
    
    Features:
    - Single interface for all MCP operations
    - Adapter lifecycle management
    - Cross-adapter workflows
    - Caching and retry logic
    - Event hooks for monitoring
    """
    
    _instance: Optional['MCPManager'] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[MCPConfig] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.config = config or MCPConfig()
        self.logger = logger.bind(component="mcp_manager")
        self._adapters: dict[AdapterType, BaseAdapter] = {}
        self._hooks: dict[str, list[Callable]] = {
            "before_request": [],
            "after_response": [],
            "on_error": [],
        }
        self._cache: dict[str, tuple[Any, float]] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all configured adapters."""
        if self._initialized:
            return
        
        self.logger.info("Initializing MCP Manager")
        
        adapter_classes = {
            AdapterType.GITHUB: GitHubAdapter,
            AdapterType.SLACK: SlackAdapter,
            AdapterType.POSTGRES: PostgresAdapter,
            AdapterType.MONITORING: MonitoringAdapter,
            AdapterType.FIGMA: FigmaAdapter,
        }
        
        for adapter_type in self.config.enabled_adapters:
            try:
                adapter_class = adapter_classes.get(adapter_type)
                if adapter_class:
                    config = self._get_adapter_config(adapter_type)
                    adapter = adapter_class(config)
                    await adapter.initialize()
                    self._adapters[adapter_type] = adapter
                    self.logger.info(f"Initialized adapter: {adapter_type}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {adapter_type}: {e}")
        
        self._initialized = True
        self.logger.info(f"MCP Manager initialized with {len(self._adapters)} adapters")
    
    async def shutdown(self) -> None:
        """Shutdown all adapters."""
        self.logger.info("Shutting down MCP Manager")
        
        for adapter_type, adapter in self._adapters.items():
            try:
                await adapter.close()
                self.logger.info(f"Closed adapter: {adapter_type}")
            except Exception as e:
                self.logger.error(f"Error closing {adapter_type}: {e}")
        
        self._adapters.clear()
        self._initialized = False
    
    def _get_adapter_config(self, adapter_type: AdapterType) -> AdapterConfig:
        """Get configuration for a specific adapter."""
        configs = {
            AdapterType.GITHUB: self.config.github,
            AdapterType.SLACK: self.config.slack,
            AdapterType.POSTGRES: self.config.postgres,
            AdapterType.MONITORING: self.config.monitoring,
            AdapterType.FIGMA: self.config.figma,
        }
        
        extra = configs.get(adapter_type, {})
        return AdapterConfig(
            adapter_type=adapter_type.value,
            timeout=self.config.default_timeout,
            retry_attempts=self.config.retry_attempts,
            extra=extra,
        )
    
    async def execute(self, request: UnifiedRequest) -> UnifiedResponse:
        """Execute a request through the appropriate adapter."""
        if not self._initialized:
            await self.initialize()
        
        # Run before hooks
        await self._run_hooks("before_request", request)
        
        adapter = self._adapters.get(request.adapter)
        if not adapter:
            return UnifiedResponse(
                success=False,
                adapter=request.adapter,
                error=f"Adapter not found or not enabled: {request.adapter}",
            )
        
        try:
            # Check cache
            cache_key = self._get_cache_key(request)
            if self.config.cache_enabled:
                cached = self._get_cached(cache_key)
                if cached is not None:
                    return cached
            
            # Execute request
            mcp_request = MCPRequest(
                method=request.method,
                params=request.params,
            )
            
            result = await adapter.execute(mcp_request)
            
            response = UnifiedResponse(
                success=result.success,
                adapter=request.adapter,
                data=result.data,
                error=result.error,
                metadata={"request_id": result.request_id},
            )
            
            # Cache successful responses
            if result.success and self.config.cache_enabled:
                self._set_cached(cache_key, response)
            
            # Run after hooks
            await self._run_hooks("after_response", response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            await self._run_hooks("on_error", e)
            return UnifiedResponse(
                success=False,
                adapter=request.adapter,
                error=str(e),
            )
    
    # ==================== Convenience Methods ====================
    
    # GitHub Operations
    async def github_create_pr(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> UnifiedResponse:
        """Create a GitHub pull request."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.GITHUB,
            method="pr.create",
            params={
                "repo": repo,
                "title": title,
                "body": body,
                "head": head,
                "base": base,
            },
        ))
    
    async def github_get_repo(self, repo: str) -> UnifiedResponse:
        """Get GitHub repository information."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.GITHUB,
            method="repo.get",
            params={"repo": repo},
        ))
    
    # Slack Operations
    async def slack_send_message(
        self,
        channel: str,
        message: str,
        blocks: Optional[list] = None,
    ) -> UnifiedResponse:
        """Send a Slack message."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.SLACK,
            method="message.send",
            params={
                "channel": channel,
                "text": message,
                "blocks": blocks,
            },
        ))
    
    async def slack_create_incident(
        self,
        title: str,
        severity: str,
        description: str,
    ) -> UnifiedResponse:
        """Create an incident channel in Slack."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.SLACK,
            method="incident.create",
            params={
                "title": title,
                "severity": severity,
                "description": description,
            },
        ))
    
    # Database Operations
    async def db_query(self, query: str, params: Optional[dict] = None) -> UnifiedResponse:
        """Execute a database query."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.POSTGRES,
            method="query.execute",
            params={"query": query, "params": params or {}},
        ))
    
    async def db_get_metrics(self) -> UnifiedResponse:
        """Get database metrics."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.POSTGRES,
            method="metrics.get",
            params={},
        ))
    
    # Monitoring Operations
    async def get_system_metrics(self) -> UnifiedResponse:
        """Get system monitoring metrics."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.MONITORING,
            method="metrics.system",
            params={},
        ))
    
    async def create_alert(
        self,
        title: str,
        severity: str,
        message: str,
    ) -> UnifiedResponse:
        """Create a monitoring alert."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.MONITORING,
            method="alert.create",
            params={
                "title": title,
                "severity": severity,
                "message": message,
            },
        ))
    
    # Figma Operations
    async def figma_get_tokens(self, file_key: str) -> UnifiedResponse:
        """Extract design tokens from Figma."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.FIGMA,
            method="tokens.extract",
            params={"file_key": file_key},
        ))
    
    async def figma_get_components(self, file_key: str) -> UnifiedResponse:
        """Get components from Figma file."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.FIGMA,
            method="file.components",
            params={"file_key": file_key},
        ))
    
    async def figma_generate_code(
        self,
        component_id: str,
        framework: str = "react",
        styling: str = "tailwind",
    ) -> UnifiedResponse:
        """Generate code from Figma component."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.FIGMA,
            method="component.to_code",
            params={
                "component_id": component_id,
                "framework": framework,
                "styling": styling,
            },
        ))
    
    async def figma_sync_design_system(
        self,
        file_key: str,
        output_dir: str = "src/styles",
    ) -> UnifiedResponse:
        """Sync design system from Figma to codebase."""
        return await self.execute(UnifiedRequest(
            adapter=AdapterType.FIGMA,
            method="sync.design_system",
            params={
                "file_key": file_key,
                "output_dir": output_dir,
            },
        ))
    
    # ==================== Cross-Adapter Workflows ====================
    
    async def design_to_code_workflow(
        self,
        figma_file: str,
        component_id: str,
        github_repo: str,
        branch: str = "feature/design-update",
    ) -> dict:
        """
        Complete design-to-code workflow.
        
        1. Extract design tokens from Figma
        2. Generate component code
        3. Create a GitHub PR with the changes
        4. Notify team on Slack
        """
        results = {}
        
        # Step 1: Get design tokens
        self.logger.info("Step 1: Extracting design tokens")
        tokens_result = await self.figma_get_tokens(figma_file)
        results["tokens"] = tokens_result
        
        if not tokens_result.success:
            return {"success": False, "error": "Failed to extract tokens", "results": results}
        
        # Step 2: Generate component code
        self.logger.info("Step 2: Generating component code")
        code_result = await self.figma_generate_code(component_id)
        results["code"] = code_result
        
        if not code_result.success:
            return {"success": False, "error": "Failed to generate code", "results": results}
        
        # Step 3: Create GitHub PR
        self.logger.info("Step 3: Creating GitHub PR")
        component_name = code_result.data.get("component_name", "Component")
        pr_result = await self.github_create_pr(
            repo=github_repo,
            title=f"feat(ui): Add {component_name} component from Figma",
            body=f"""## Design System Update

### Changes
- Added `{component_name}` component generated from Figma design
- Updated design tokens

### Figma Reference
File: `{figma_file}`
Component: `{component_id}`

### Generated Files
- `src/components/{component_name}.tsx`
- `src/styles/tokens.css`
""",
            head=branch,
            base="main",
        )
        results["pr"] = pr_result
        
        # Step 4: Notify on Slack
        self.logger.info("Step 4: Sending Slack notification")
        slack_result = await self.slack_send_message(
            channel="#design-system",
            message=f"🎨 New component `{component_name}` generated from Figma!",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Design System Update*\n\nNew component `{component_name}` has been generated from Figma and a PR has been created."
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View PR"},
                            "url": pr_result.data.get("url", "#") if pr_result.success else "#",
                        }
                    ]
                }
            ]
        )
        results["notification"] = slack_result
        
        return {
            "success": True,
            "workflow": "design_to_code",
            "results": results,
        }
    
    async def incident_response_workflow(
        self,
        alert_title: str,
        severity: str,
        affected_service: str,
    ) -> dict:
        """
        Automated incident response workflow.
        
        1. Create monitoring alert
        2. Create Slack incident channel
        3. Query related database metrics
        4. Generate incident report
        """
        results = {}
        
        # Step 1: Create alert
        alert_result = await self.create_alert(
            title=alert_title,
            severity=severity,
            message=f"Incident detected in {affected_service}",
        )
        results["alert"] = alert_result
        
        # Step 2: Create incident channel
        incident_result = await self.slack_create_incident(
            title=alert_title,
            severity=severity,
            description=f"Automated incident for {affected_service}",
        )
        results["incident_channel"] = incident_result
        
        # Step 3: Get system metrics
        metrics_result = await self.get_system_metrics()
        results["metrics"] = metrics_result
        
        # Step 4: Get database metrics
        db_metrics = await self.db_get_metrics()
        results["db_metrics"] = db_metrics
        
        return {
            "success": True,
            "workflow": "incident_response",
            "results": results,
        }
    
    # ==================== Hook Management ====================
    
    def add_hook(self, event: str, callback: Callable) -> None:
        """Add a hook for an event."""
        if event in self._hooks:
            self._hooks[event].append(callback)
    
    def remove_hook(self, event: str, callback: Callable) -> None:
        """Remove a hook for an event."""
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
    
    async def _run_hooks(self, event: str, data: Any) -> None:
        """Run all hooks for an event."""
        for hook in self._hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(data)
                else:
                    hook(data)
            except Exception as e:
                self.logger.error(f"Hook error: {e}")
    
    # ==================== Cache Management ====================
    
    def _get_cache_key(self, request: UnifiedRequest) -> str:
        """Generate cache key for a request."""
        import hashlib
        import json
        
        key_data = f"{request.adapter}:{request.method}:{json.dumps(request.params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[UnifiedResponse]:
        """Get cached response if valid."""
        import time
        
        if key in self._cache:
            response, timestamp = self._cache[key]
            if time.time() - timestamp < self.config.cache_ttl:
                return response
            del self._cache[key]
        return None
    
    def _set_cached(self, key: str, response: UnifiedResponse) -> None:
        """Cache a response."""
        import time
        
        self._cache[key] = (response, time.time())
    
    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
    
    # ==================== Status & Health ====================
    
    async def health_check(self) -> dict:
        """Check health of all adapters."""
        health = {
            "status": "healthy",
            "adapters": {},
        }
        
        for adapter_type, adapter in self._adapters.items():
            try:
                adapter_health = await adapter.health_check()
                health["adapters"][adapter_type.value] = {
                    "status": "healthy" if adapter_health else "unhealthy",
                }
            except Exception as e:
                health["adapters"][adapter_type.value] = {
                    "status": "error",
                    "error": str(e),
                }
                health["status"] = "degraded"
        
        return health
    
    def get_adapter(self, adapter_type: AdapterType) -> Optional[BaseAdapter]:
        """Get a specific adapter instance."""
        return self._adapters.get(adapter_type)
    
    @property
    def available_adapters(self) -> list[AdapterType]:
        """Get list of available adapters."""
        return list(self._adapters.keys())


# Global MCP manager instance
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager instance."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


async def init_mcp(config: Optional[MCPConfig] = None) -> MCPManager:
    """Initialize the global MCP manager."""
    global _mcp_manager
    _mcp_manager = MCPManager(config)
    await _mcp_manager.initialize()
    return _mcp_manager
