"""
Tests for Orchestrator

Unit tests for the agent orchestrator.
"""

import pytest
import asyncio
from src.core.orchestrator import (
    Orchestrator,
    TaskRequest,
    TaskResult,
    TaskStatus,
    AgentRegistry,
)
from src.core.message_queue import MessagePriority


class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.processed = []
    
    async def process(self, message):
        """Process a message."""
        from agents.specialists import AgentResponse
        
        self.processed.append(message)
        return AgentResponse(
            success=True,
            message_id=message.id,
            agent_name=self.name,
            action=message.action,
            result={"mock": "result"},
            duration_ms=10,
        )
    
    async def initialize(self):
        pass
    
    def get_metrics(self):
        return {"processed": len(self.processed)}
    
    async def health_check(self):
        return {"status": "healthy"}


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        agent = MockAgent("test_agent")
        
        registry.register("test_agent", agent, ["cap1", "cap2"])
        
        assert registry.get("test_agent") == agent
    
    def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = AgentRegistry()
        agent = MockAgent("test_agent")
        
        registry.register("test_agent", agent, ["cap1"])
        registry.unregister("test_agent")
        
        assert registry.get("test_agent") is None
    
    def test_get_by_capability(self):
        """Test getting agents by capability."""
        registry = AgentRegistry()
        
        registry.register("agent1", MockAgent("agent1"), ["cap1", "cap2"])
        registry.register("agent2", MockAgent("agent2"), ["cap2", "cap3"])
        
        agents_with_cap2 = registry.get_by_capability("cap2")
        
        assert "agent1" in agents_with_cap2
        assert "agent2" in agents_with_cap2
    
    def test_list_agents(self):
        """Test listing all agents."""
        registry = AgentRegistry()
        
        registry.register("agent1", MockAgent("agent1"), ["cap1"])
        registry.register("agent2", MockAgent("agent2"), ["cap2"])
        
        agents = registry.list_agents()
        
        assert len(agents) == 2
        assert any(a["name"] == "agent1" for a in agents)


class TestTaskRequest:
    """Tests for TaskRequest."""
    
    def test_task_request_defaults(self):
        """Test default task request values."""
        request = TaskRequest(action="test_action")
        
        assert request.id is not None
        assert request.action == "test_action"
        assert request.payload == {}
        assert request.priority == MessagePriority.MEDIUM
        assert request.timeout_seconds == 300
    
    def test_task_request_custom(self):
        """Test custom task request values."""
        request = TaskRequest(
            action="custom_action",
            payload={"key": "value"},
            target_agent="specific_agent",
            priority=MessagePriority.HIGH,
            timeout_seconds=600,
        )
        
        assert request.action == "custom_action"
        assert request.payload["key"] == "value"
        assert request.target_agent == "specific_agent"
        assert request.priority == MessagePriority.HIGH


class TestOrchestrator:
    """Tests for Orchestrator."""
    
    @pytest.fixture
    async def orchestrator(self):
        """Create an orchestrator for testing."""
        orch = Orchestrator(max_concurrent_tasks=5)
        await orch.start()
        yield orch
        await orch.stop()
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        return MockAgent("mock_agent")
    
    @pytest.mark.asyncio
    async def test_orchestrator_start_stop(self):
        """Test orchestrator start and stop."""
        orch = Orchestrator()
        
        await orch.start()
        assert orch._shutdown is False
        
        await orch.stop()
        assert orch._shutdown is True
    
    @pytest.mark.asyncio
    async def test_register_agent(self, orchestrator, mock_agent):
        """Test registering an agent."""
        orchestrator.register_agent(
            "mock_agent",
            mock_agent,
            ["mock_capability"],
        )
        
        assert orchestrator.registry.get("mock_agent") == mock_agent
    
    @pytest.mark.asyncio
    async def test_submit_task(self, orchestrator, mock_agent):
        """Test submitting a task."""
        orchestrator.register_agent("mock_agent", mock_agent, ["test"])
        
        request = TaskRequest(
            action="test_action",
            target_agent="mock_agent",
        )
        
        task_id = await orchestrator.submit_task(request)
        
        assert task_id is not None
        assert task_id == request.id
    
    @pytest.mark.asyncio
    async def test_task_routing_security(self, orchestrator, mock_agent):
        """Test automatic routing to security agent."""
        orchestrator.register_agent("security_agent", mock_agent, ["scan"])
        
        request = TaskRequest(action="scan_vulnerabilities")
        
        # The orchestrator should route to security_agent
        routed_agent = orchestrator._route_task(request)
        
        assert routed_agent == "security_agent"
    
    @pytest.mark.asyncio
    async def test_task_routing_testing(self, orchestrator, mock_agent):
        """Test automatic routing to testing agent."""
        orchestrator.register_agent("testing_agent", mock_agent, ["test"])
        
        request = TaskRequest(action="generate_tests")
        
        routed_agent = orchestrator._route_task(request)
        
        assert routed_agent == "testing_agent"
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, orchestrator):
        """Test getting orchestrator metrics."""
        metrics = orchestrator.get_metrics()
        
        assert "total_tasks" in metrics
        assert "completed_tasks" in metrics
        assert "failed_tasks" in metrics
        assert "running_tasks" in metrics
        assert "queued_tasks" in metrics
        assert "success_rate" in metrics
    
    @pytest.mark.asyncio
    async def test_health_check(self, orchestrator):
        """Test orchestrator health check."""
        health = await orchestrator.health_check()
        
        assert "status" in health
        assert "metrics" in health
        assert health["status"] == "healthy"
