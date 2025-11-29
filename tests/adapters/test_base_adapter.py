"""
Tests for Base Adapter

Unit tests for the base MCP adapter functionality.
"""

import pytest
from mcp.adapters.base_adapter import (
    BaseAdapter,
    AdapterConfig,
    MCPRequest,
    MCPResponse,
)


class ConcreteAdapter(BaseAdapter):
    """Concrete implementation for testing abstract BaseAdapter."""
    
    async def _setup_client(self) -> None:
        self._client = "test_client"
    
    async def _cleanup(self) -> None:
        self._client = None
    
    async def execute(self, request: MCPRequest) -> MCPResponse:
        if request.method == "test_method":
            return MCPResponse(
                success=True,
                data={"result": "success"},
                request_id=request.request_id,
            )
        return MCPResponse(
            success=False,
            error=f"Unknown method: {request.method}",
            request_id=request.request_id,
        )


class TestAdapterConfig:
    """Tests for AdapterConfig."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = AdapterConfig(name="test")
        
        assert config.name == "test"
        assert config.enabled is True
        assert config.timeout == 30
        assert config.retry_attempts == 3
        assert config.capabilities == []
    
    def test_config_custom_values(self):
        """Test custom configuration values."""
        config = AdapterConfig(
            name="custom",
            enabled=False,
            timeout=60,
            retry_attempts=5,
            capabilities=["read", "write"],
            extra={"api_key": "test"},
        )
        
        assert config.name == "custom"
        assert config.enabled is False
        assert config.timeout == 60
        assert config.retry_attempts == 5
        assert "read" in config.capabilities
        assert config.extra["api_key"] == "test"


class TestMCPRequest:
    """Tests for MCPRequest."""
    
    def test_request_defaults(self):
        """Test default request values."""
        request = MCPRequest(method="test", params={})
        
        assert request.method == "test"
        assert request.params == {}
        assert request.request_id is None
    
    def test_request_with_params(self):
        """Test request with parameters."""
        request = MCPRequest(
            method="query",
            params={"table": "users", "limit": 10},
            request_id="req-123",
        )
        
        assert request.method == "query"
        assert request.params["table"] == "users"
        assert request.request_id == "req-123"


class TestMCPResponse:
    """Tests for MCPResponse."""
    
    def test_success_response(self):
        """Test successful response."""
        response = MCPResponse(
            success=True,
            data={"result": "data"},
            request_id="req-123",
        )
        
        assert response.success is True
        assert response.data["result"] == "data"
        assert response.error is None
    
    def test_error_response(self):
        """Test error response."""
        response = MCPResponse(
            success=False,
            error="Something went wrong",
            request_id="req-123",
        )
        
        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.data is None


class TestBaseAdapter:
    """Tests for BaseAdapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create a concrete adapter for testing."""
        config = AdapterConfig(
            name="test_adapter",
            capabilities=["test_capability"],
        )
        return ConcreteAdapter(config)
    
    @pytest.mark.asyncio
    async def test_initialize(self, adapter):
        """Test adapter initialization."""
        await adapter.initialize()
        
        assert adapter._initialized is True
        assert adapter._client == "test_client"
    
    @pytest.mark.asyncio
    async def test_shutdown(self, adapter):
        """Test adapter shutdown."""
        await adapter.initialize()
        await adapter.shutdown()
        
        assert adapter._initialized is False
        assert adapter._client is None
    
    @pytest.mark.asyncio
    async def test_execute_success(self, adapter):
        """Test successful execution."""
        await adapter.initialize()
        
        request = MCPRequest(method="test_method", params={})
        response = await adapter.execute(request)
        
        assert response.success is True
        assert response.data["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_execute_unknown_method(self, adapter):
        """Test execution with unknown method."""
        await adapter.initialize()
        
        request = MCPRequest(method="unknown", params={})
        response = await adapter.execute(request)
        
        assert response.success is False
        assert "Unknown method" in response.error
    
    def test_has_capability(self, adapter):
        """Test capability checking."""
        assert adapter.has_capability("test_capability")
        assert not adapter.has_capability("other_capability")
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test health check."""
        result = await adapter.health_check()
        
        # Not initialized, should return False
        assert result is False
        
        await adapter.initialize()
        result = await adapter.health_check()
        
        assert result is True
