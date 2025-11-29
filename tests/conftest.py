"""
Pytest Configuration and Fixtures

Shared fixtures for all tests.
"""

import asyncio
import pytest
from typing import Generator, AsyncGenerator


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def agent_config():
    """Create a test agent configuration."""
    from agents.specialists import AgentConfig
    
    return AgentConfig(
        name="test_agent",
        agent_type="specialist",
        model="test-model",
        capabilities=["test_capability"],
        settings={"test_setting": True},
    )


@pytest.fixture
def agent_message():
    """Create a test agent message."""
    from agents.specialists import AgentMessage
    
    return AgentMessage(
        action="test_action",
        payload={"key": "value"},
    )


@pytest.fixture
async def security_agent(agent_config):
    """Create a security agent for testing."""
    from agents.specialists import SecurityAgent, AgentConfig
    
    config = AgentConfig(
        name="security_agent",
        agent_type="specialist",
        capabilities=["vulnerability_scanning", "secrets_detection"],
    )
    agent = SecurityAgent(config)
    await agent.initialize()
    yield agent
    await agent.shutdown() if hasattr(agent, 'shutdown') else None


@pytest.fixture
async def testing_agent(agent_config):
    """Create a testing agent for testing."""
    from agents.specialists import TestingAgent, AgentConfig
    
    config = AgentConfig(
        name="testing_agent",
        agent_type="specialist",
        capabilities=["test_generation", "coverage_analysis"],
    )
    agent = TestingAgent(config)
    await agent.initialize()
    yield agent


@pytest.fixture
async def orchestrator():
    """Create an orchestrator for testing."""
    from src.core import Orchestrator
    
    orch = Orchestrator(max_concurrent_tasks=5)
    await orch.start()
    yield orch
    await orch.stop()


@pytest.fixture
def message_queue():
    """Create a message queue for testing."""
    from src.core import MessageQueue
    
    return MessageQueue(max_size=100)


@pytest.fixture
def mock_api_client(mocker):
    """Create a mock API client."""
    import httpx
    
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    
    mock_client = mocker.MagicMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    
    return mock_client
