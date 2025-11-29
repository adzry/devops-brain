"""
DevOps Brain SDK Client

Main client for interacting with DevOps Brain API.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from .exceptions import (
    AuthenticationError,
    DevOpsBrainError,
    RateLimitError,
    TaskError,
)

logger = logging.getLogger(__name__)


@dataclass
class ClientConfig:
    """SDK client configuration."""
    base_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    timeout: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True


class DevOpsBrainClient:
    """
    Main SDK client for DevOps Brain.
    
    Usage:
        async with DevOpsBrainClient(config) as client:
            result = await client.execute("scan_vulnerabilities", {"target": "src/"})
    """
    
    def __init__(self, config: Optional[ClientConfig] = None):
        self.config = config or ClientConfig()
        self._client: Optional[httpx.AsyncClient] = None
        
        # Sub-clients
        self._agents: Optional["AgentClient"] = None
        self._tasks: Optional["TaskClient"] = None
    
    async def __aenter__(self) -> "DevOpsBrainClient":
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self) -> None:
        """Initialize the HTTP client."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=headers,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        )
        
        # Verify connection
        await self.health_check()
        logger.info(f"Connected to DevOps Brain at {self.config.base_url}")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """Make an API request with retry logic."""
        if not self._client:
            raise DevOpsBrainError("Client not connected. Call connect() first.")
        
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                if method == "GET":
                    response = await self._client.get(endpoint, params=params)
                elif method == "POST":
                    response = await self._client.post(endpoint, json=data)
                elif method == "PUT":
                    response = await self._client.put(endpoint, json=data)
                elif method == "DELETE":
                    response = await self._client.delete(endpoint)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                # Handle response
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key", status_code=401)
                elif response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 60))
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after,
                        status_code=429,
                    )
                else:
                    error_data = response.json() if response.content else {}
                    raise DevOpsBrainError(
                        error_data.get("detail", f"Request failed: {response.status_code}"),
                        status_code=response.status_code,
                        response=error_data,
                    )
                    
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                raise DevOpsBrainError(f"Network error: {e}")
            
            except RateLimitError:
                raise
        
        raise DevOpsBrainError(f"Request failed after {self.config.max_retries} attempts: {last_error}")
    
    # ========================================================================
    # Core Methods
    # ========================================================================
    
    async def health_check(self) -> dict:
        """Check API health."""
        return await self._request("GET", "/health")
    
    async def execute(
        self,
        action: str,
        payload: Optional[dict] = None,
        agent: Optional[str] = None,
        priority: str = "medium",
        timeout: int = 300,
    ) -> dict:
        """
        Execute an action.
        
        Args:
            action: Action to execute
            payload: Action parameters
            agent: Target agent (auto-routed if not specified)
            priority: Task priority
            timeout: Execution timeout
            
        Returns:
            Task result
        """
        data = {
            "action": action,
            "payload": payload or {},
            "target_agent": agent,
            "priority": priority,
            "timeout_seconds": timeout,
        }
        
        return await self._request("POST", "/api/v1/execute", data)
    
    async def submit_task(
        self,
        action: str,
        payload: Optional[dict] = None,
        agent: Optional[str] = None,
        priority: str = "medium",
    ) -> str:
        """
        Submit a task for async execution.
        
        Returns:
            Task ID
        """
        data = {
            "action": action,
            "payload": payload or {},
            "target_agent": agent,
            "priority": priority,
        }
        
        result = await self._request("POST", "/api/v1/tasks/submit", data)
        return result["task_id"]
    
    async def wait_for_task(self, task_id: str, timeout: int = 300) -> dict:
        """Wait for a task to complete."""
        return await self._request(
            "POST",
            f"/api/v1/tasks/{task_id}/wait",
            params={"timeout": timeout},
        )
    
    # ========================================================================
    # Sub-clients
    # ========================================================================
    
    @property
    def agents(self) -> "AgentClient":
        """Get agent sub-client."""
        if self._agents is None:
            from .agents import AgentClient
            self._agents = AgentClient(self)
        return self._agents
    
    @property
    def tasks(self) -> "TaskClient":
        """Get task sub-client."""
        if self._tasks is None:
            from .tasks import TaskClient
            self._tasks = TaskClient(self)
        return self._tasks
    
    # ========================================================================
    # Convenience Methods
    # ========================================================================
    
    async def scan_security(
        self,
        target: str = ".",
        scan_type: str = "full",
    ) -> dict:
        """Run a security scan."""
        return await self.execute(
            action="scan_vulnerabilities",
            payload={"target": target, "scan_type": scan_type},
            agent="security_agent",
        )
    
    async def generate_tests(
        self,
        file: str,
        framework: str = "pytest",
    ) -> dict:
        """Generate tests for a file."""
        return await self.execute(
            action="generate_tests",
            payload={"file": file, "framework": framework},
            agent="testing_agent",
        )
    
    async def analyze_performance(
        self,
        target: str = ".",
    ) -> dict:
        """Analyze performance."""
        return await self.execute(
            action="profile_application",
            payload={"target": target},
            agent="performance_agent",
        )
    
    async def detect_drift(self) -> dict:
        """Detect infrastructure drift."""
        return await self.execute(
            action="detect_drift",
            payload={},
            agent="infrastructure_agent",
        )
