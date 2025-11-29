"""
Agent Client

SDK client for agent operations.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .client import DevOpsBrainClient


class AgentClient:
    """Client for agent operations."""
    
    def __init__(self, client: "DevOpsBrainClient"):
        self._client = client
    
    async def list(self) -> list[dict]:
        """List all agents."""
        result = await self._client._request("GET", "/api/v1/agents")
        return result.get("agents", [])
    
    async def get(self, name: str) -> dict:
        """Get agent information."""
        return await self._client._request("GET", f"/api/v1/agents/{name}")
    
    async def execute(
        self,
        name: str,
        action: str,
        payload: Optional[dict] = None,
    ) -> dict:
        """Execute an action on a specific agent."""
        data = {"action": action, "payload": payload or {}}
        return await self._client._request(
            "POST",
            f"/api/v1/agents/{name}/execute",
            data,
        )
    
    async def health(self, name: str) -> dict:
        """Get agent health status."""
        return await self._client._request("GET", f"/api/v1/agents/{name}/health")
    
    async def capabilities(self, name: str) -> list[str]:
        """Get agent capabilities."""
        result = await self._client._request(
            "GET",
            f"/api/v1/agents/{name}/capabilities",
        )
        return result.get("capabilities", [])
    
    # ========================================================================
    # Agent-specific Methods
    # ========================================================================
    
    async def security_scan(
        self,
        target: str,
        scan_type: str = "full",
    ) -> dict:
        """Run security scan."""
        return await self.execute(
            "security_agent",
            "scan_vulnerabilities",
            {"target": target, "scan_type": scan_type},
        )
    
    async def detect_secrets(self, target: str) -> dict:
        """Detect secrets in code."""
        return await self.execute(
            "security_agent",
            "detect_secrets",
            {"target": target},
        )
    
    async def check_compliance(self, frameworks: list[str]) -> dict:
        """Check compliance against frameworks."""
        return await self.execute(
            "security_agent",
            "check_compliance",
            {"frameworks": frameworks},
        )
    
    async def generate_tests(
        self,
        file: str,
        framework: str = "pytest",
    ) -> dict:
        """Generate tests."""
        return await self.execute(
            "testing_agent",
            "generate_tests",
            {"file": file, "framework": framework},
        )
    
    async def analyze_coverage(self, target: str) -> dict:
        """Analyze test coverage."""
        return await self.execute(
            "testing_agent",
            "analyze_coverage",
            {"target": target},
        )
    
    async def generate_docs(
        self,
        source: str,
        format: str = "openapi",
    ) -> dict:
        """Generate API documentation."""
        return await self.execute(
            "documentation_agent",
            "generate_api_docs",
            {"source": source, "format": format},
        )
    
    async def profile_performance(self, target: str) -> dict:
        """Profile application performance."""
        return await self.execute(
            "performance_agent",
            "profile_application",
            {"target": target},
        )
    
    async def triage_incident(self, alert: dict) -> dict:
        """Triage an incident."""
        return await self.execute(
            "incident_response_agent",
            "triage_incident",
            {"alert": alert},
        )
    
    async def optimize_queries(self, queries: list[str]) -> dict:
        """Optimize database queries."""
        return await self.execute(
            "database_agent",
            "optimize_queries",
            {"queries": queries},
        )
    
    async def analyze_costs(self, time_range: str = "30d") -> dict:
        """Analyze infrastructure costs."""
        return await self.execute(
            "infrastructure_agent",
            "analyze_costs",
            {"time_range": time_range},
        )
