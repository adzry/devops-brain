"""
Tests for Security Agent

Unit tests for the security agent functionality.
"""

import pytest
from agents.specialists import SecurityAgent, AgentConfig, AgentMessage


class TestSecurityAgent:
    """Tests for SecurityAgent."""
    
    @pytest.fixture
    def security_agent(self):
        """Create a security agent for testing."""
        config = AgentConfig(
            name="security_agent",
            agent_type="specialist",
            capabilities=[
                "vulnerability_scanning",
                "secrets_detection",
                "compliance_checking",
            ],
        )
        return SecurityAgent(config)
    
    def test_agent_initialization(self, security_agent):
        """Test security agent initialization."""
        assert security_agent.name == "security_agent"
        assert "vulnerability_scanning" in security_agent.capabilities
    
    def test_handlers_registered(self, security_agent):
        """Test that all handlers are registered."""
        expected_handlers = [
            "scan_vulnerabilities",
            "scan_dependencies",
            "detect_secrets",
            "check_compliance",
            "threat_model",
            "generate_advisory",
            "assess_risk",
        ]
        
        for handler in expected_handlers:
            assert handler in security_agent._handlers
    
    @pytest.mark.asyncio
    async def test_scan_vulnerabilities(self, security_agent):
        """Test vulnerability scanning."""
        message = AgentMessage(
            action="scan_vulnerabilities",
            payload={"target": "src/", "scan_type": "full"},
        )
        
        response = await security_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "vulnerabilities_found" in response.result
        assert "by_severity" in response.result
    
    @pytest.mark.asyncio
    async def test_scan_dependencies(self, security_agent):
        """Test dependency scanning."""
        message = AgentMessage(
            action="scan_dependencies",
            payload={"manifest": "requirements.txt"},
        )
        
        response = await security_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "vulnerable_dependencies" in response.result
    
    @pytest.mark.asyncio
    async def test_detect_secrets(self, security_agent):
        """Test secrets detection."""
        message = AgentMessage(
            action="detect_secrets",
            payload={"target": "."},
        )
        
        response = await security_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "secrets_found" in response.result
    
    @pytest.mark.asyncio
    async def test_check_compliance(self, security_agent):
        """Test compliance checking."""
        message = AgentMessage(
            action="check_compliance",
            payload={"frameworks": ["OWASP", "SOC2"]},
        )
        
        response = await security_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "frameworks_checked" in response.result
    
    @pytest.mark.asyncio
    async def test_threat_model(self, security_agent):
        """Test threat modeling."""
        message = AgentMessage(
            action="threat_model",
            payload={"system": "web_application"},
        )
        
        response = await security_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "threats_identified" in response.result
        assert "methodology" in response.result
    
    @pytest.mark.asyncio
    async def test_assess_risk(self, security_agent):
        """Test risk assessment."""
        message = AgentMessage(
            action="assess_risk",
            payload={"scope": "full"},
        )
        
        response = await security_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "overall_risk_score" in response.result
        assert "risk_level" in response.result
    
    @pytest.mark.asyncio
    async def test_generate_advisory(self, security_agent):
        """Test advisory generation."""
        message = AgentMessage(
            action="generate_advisory",
            payload={"vulnerability_id": "VULN-001"},
        )
        
        response = await security_agent.process(message)
        
        assert response.success
        assert response.result is not None
        assert "advisory_id" in response.result
        assert "severity" in response.result
    
    @pytest.mark.asyncio
    async def test_recommendations_included(self, security_agent):
        """Test that recommendations are included in responses."""
        message = AgentMessage(
            action="scan_vulnerabilities",
            payload={"target": "src/"},
        )
        
        response = await security_agent.process(message)
        
        assert response.success
        assert len(response.recommendations) > 0
