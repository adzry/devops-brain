"""
Tests for Base Agent

Unit tests for the base agent functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agents.specialists.base_agent import (
    BaseAgent,
    AgentConfig,
    AgentMessage,
    AgentResponse,
    AgentStatus,
    TaskPriority,
)


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing abstract BaseAgent."""
    
    def _register_handlers(self) -> None:
        self.register_handler("test_action", self._test_handler)
        self.register_handler("failing_action", self._failing_handler)
    
    async def _get_system_prompt(self) -> str:
        return "Test system prompt"
    
    async def _test_handler(self, payload: dict) -> dict:
        return {"data": {"result": "success"}, "recommendations": ["test"]}
    
    async def _failing_handler(self, payload: dict) -> dict:
        raise ValueError("Test error")


class TestAgentConfig:
    """Tests for AgentConfig."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = AgentConfig(name="test", agent_type="specialist")
        
        assert config.name == "test"
        assert config.agent_type == "specialist"
        assert config.model == "gpt-5.1-codex-high"
        assert config.capabilities == []
        assert config.settings == {}
        assert config.max_retries == 3
        assert config.timeout_seconds == 300
    
    def test_config_custom_values(self):
        """Test custom configuration values."""
        config = AgentConfig(
            name="custom",
            agent_type="orchestrator",
            model="custom-model",
            capabilities=["cap1", "cap2"],
            settings={"key": "value"},
            max_retries=5,
            timeout_seconds=600,
        )
        
        assert config.name == "custom"
        assert config.model == "custom-model"
        assert "cap1" in config.capabilities
        assert config.settings["key"] == "value"
        assert config.max_retries == 5


class TestAgentMessage:
    """Tests for AgentMessage."""
    
    def test_message_defaults(self):
        """Test default message values."""
        message = AgentMessage()
        
        assert message.id is not None
        assert message.action == ""
        assert message.payload == {}
        assert message.priority == TaskPriority.MEDIUM
    
    def test_message_custom_values(self):
        """Test custom message values."""
        message = AgentMessage(
            action="test_action",
            payload={"key": "value"},
            priority=TaskPriority.HIGH,
        )
        
        assert message.action == "test_action"
        assert message.payload["key"] == "value"
        assert message.priority == TaskPriority.HIGH


class TestBaseAgent:
    """Tests for BaseAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create a concrete agent for testing."""
        config = AgentConfig(
            name="test_agent",
            agent_type="specialist",
            capabilities=["test_capability"],
        )
        return ConcreteAgent(config)
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "test_agent"
        assert agent.status == AgentStatus.IDLE
        assert "test_capability" in agent.capabilities
    
    def test_has_capability(self, agent):
        """Test capability checking."""
        assert agent.has_capability("test_capability")
        assert not agent.has_capability("unknown_capability")
    
    def test_register_handler(self, agent):
        """Test handler registration."""
        assert "test_action" in agent._handlers
        assert "failing_action" in agent._handlers
    
    @pytest.mark.asyncio
    async def test_process_success(self, agent):
        """Test successful message processing."""
        message = AgentMessage(
            action="test_action",
            payload={"key": "value"},
        )
        
        response = await agent.process(message)
        
        assert response.success
        assert response.agent_name == "test_agent"
        assert response.action == "test_action"
        assert response.result == {"result": "success"}
        assert response.error is None
        assert response.duration_ms >= 0
    
    @pytest.mark.asyncio
    async def test_process_failure(self, agent):
        """Test failed message processing."""
        message = AgentMessage(action="failing_action")
        
        response = await agent.process(message)
        
        assert not response.success
        assert "Test error" in response.error
    
    @pytest.mark.asyncio
    async def test_process_unknown_action(self, agent):
        """Test processing with unknown action."""
        message = AgentMessage(action="unknown_action")
        
        response = await agent.process(message)
        
        assert not response.success
        assert "Unknown action" in response.error
    
    def test_get_metrics(self, agent):
        """Test metrics retrieval."""
        metrics = agent.get_metrics()
        
        assert "agent_name" in metrics
        assert "status" in metrics
        assert "tasks_completed" in metrics
        assert "tasks_failed" in metrics
        assert "success_rate" in metrics
    
    @pytest.mark.asyncio
    async def test_health_check(self, agent):
        """Test health check."""
        health = await agent.health_check()
        
        assert "agent" in health
        assert "status" in health
        assert health["agent"] == "test_agent"
    
    @pytest.mark.asyncio
    async def test_send_message(self, agent):
        """Test sending a message to another agent."""
        message = await agent.send_message(
            recipient="other_agent",
            action="some_action",
            payload={"data": "test"},
            priority=TaskPriority.HIGH,
        )
        
        assert message.sender == "test_agent"
        assert message.recipient == "other_agent"
        assert message.action == "some_action"
        assert message.priority == TaskPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_metrics_update_on_success(self, agent):
        """Test that metrics are updated after successful processing."""
        message = AgentMessage(action="test_action")
        
        await agent.process(message)
        
        metrics = agent.get_metrics()
        assert metrics["tasks_completed"] == 1
        assert metrics["tasks_failed"] == 0
    
    @pytest.mark.asyncio
    async def test_metrics_update_on_failure(self, agent):
        """Test that metrics are updated after failed processing."""
        message = AgentMessage(action="failing_action")
        
        await agent.process(message)
        
        metrics = agent.get_metrics()
        assert metrics["tasks_completed"] == 0
        assert metrics["tasks_failed"] == 1
