"""
Base Adapter for MCP Integration

Provides the foundation for all MCP adapters with common functionality
for authentication, error handling, and protocol compliance.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AdapterConfig:
    """Configuration for an MCP adapter."""
    
    name: str
    enabled: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    capabilities: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPRequest:
    """Represents an MCP protocol request."""
    
    method: str
    params: dict[str, Any]
    request_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None


@dataclass
class MCPResponse:
    """Represents an MCP protocol response."""
    
    success: bool
    data: Any = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    """
    Abstract base class for MCP adapters.
    
    All service adapters should inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, config: AdapterConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self._initialized = False
        self._client: Any = None
    
    async def initialize(self) -> None:
        """Initialize the adapter and establish connections."""
        if self._initialized:
            return
        
        self.logger.info(f"Initializing adapter: {self.config.name}")
        await self._setup_client()
        self._initialized = True
        self.logger.info(f"Adapter initialized: {self.config.name}")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the adapter."""
        if not self._initialized:
            return
            
        self.logger.info(f"Shutting down adapter: {self.config.name}")
        await self._cleanup()
        self._initialized = False
    
    @abstractmethod
    async def _setup_client(self) -> None:
        """Set up the underlying service client."""
        pass
    
    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up resources."""
        pass
    
    @abstractmethod
    async def execute(self, request: MCPRequest) -> MCPResponse:
        """Execute an MCP request."""
        pass
    
    def has_capability(self, capability: str) -> bool:
        """Check if the adapter has a specific capability."""
        return capability in self.config.capabilities
    
    async def health_check(self) -> bool:
        """Check if the adapter is healthy and connected."""
        try:
            return await self._health_check_impl()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def _health_check_impl(self) -> bool:
        """Implementation-specific health check."""
        return self._initialized
    
    async def _retry_operation(
        self,
        operation: callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with retry logic."""
        last_error = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff
                self.logger.warning(
                    f"Operation failed (attempt {attempt + 1}/"
                    f"{self.config.retry_attempts}): {e}"
                )
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(wait_time)
        
        raise last_error
