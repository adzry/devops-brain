"""
Tests for Testing Agent

Unit tests for the testing agent functionality.
"""

import pytest
from agents.specialists import TestingAgent, AgentConfig, AgentMessage


class TestTestingAgent:
    """Tests for TestingAgent."""
    
    @pytest.fixture
    def testing_agent(self):
        """Create a testing agent for testing."""
        config = AgentConfig(
            name="testing_agent",
            agent_type="specialist",
            capabilities=[
                "test_generation",
                "test_execution",
                "coverage_analysis",
            ],
        )
        return TestingAgent(config)
    
    def test_agent_initialization(self, testing_agent):
        """Test testing agent initialization."""
        assert testing_agent.name == "testing_agent"
        assert "test_generation" in testing_agent.capabilities
    
    def test_handlers_registered(self, testing_agent):
        """Test that all handlers are registered."""
        expected_handlers = [
            "generate_tests",
            "run_tests",
            "analyze_coverage",
            "detect_flaky",
            "mutation_test",
            "optimize_suite",
            "suggest_tests",
        ]
        
        for handler in expected_handlers:
            assert handler in testing_agent._handlers
    
    @pytest.mark.asyncio
    async def test_generate_tests(self, testing_agent):
        """Test test generation."""
        message = AgentMessage(
            action="generate_tests",
            payload={"file": "src/calculator.py", "framework": "pytest"},
        )
        
        response = await testing_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "tests_generated" in response.result
        assert "test_code" in response.result
    
    @pytest.mark.asyncio
    async def test_run_tests(self, testing_agent):
        """Test test execution."""
        message = AgentMessage(
            action="run_tests",
            payload={"path": "tests/", "type": "unit"},
        )
        
        response = await testing_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "total_tests" in response.result
        assert "passed" in response.result
        assert "failed" in response.result
    
    @pytest.mark.asyncio
    async def test_analyze_coverage(self, testing_agent):
        """Test coverage analysis."""
        message = AgentMessage(
            action="analyze_coverage",
            payload={"target": "src/"},
        )
        
        response = await testing_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "overall_coverage" in response.result
        assert "by_file" in response.result
    
    @pytest.mark.asyncio
    async def test_detect_flaky(self, testing_agent):
        """Test flaky test detection."""
        message = AgentMessage(
            action="detect_flaky",
            payload={"runs": 10},
        )
        
        response = await testing_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "flaky_count" in response.result
        assert "flaky_tests" in response.result
    
    @pytest.mark.asyncio
    async def test_mutation_test(self, testing_agent):
        """Test mutation testing."""
        message = AgentMessage(
            action="mutation_test",
            payload={"target": "src/"},
        )
        
        response = await testing_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "mutation_score" in response.result
        assert "mutations_killed" in response.result
    
    @pytest.mark.asyncio
    async def test_optimize_suite(self, testing_agent):
        """Test suite optimization."""
        message = AgentMessage(
            action="optimize_suite",
            payload={},
        )
        
        response = await testing_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "optimizations" in response.result
        assert "improvement_percent" in response.result
    
    @pytest.mark.asyncio
    async def test_suggest_tests(self, testing_agent):
        """Test test suggestion."""
        message = AgentMessage(
            action="suggest_tests",
            payload={"files": ["src/api.py"]},
        )
        
        response = await testing_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "suggested_tests" in response.result
