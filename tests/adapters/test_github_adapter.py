"""
Tests for GitHub Adapter

Unit tests for the GitHub MCP adapter.
"""

import pytest
from mcp.adapters import GitHubAdapter
from mcp.adapters.base_adapter import AdapterConfig, MCPRequest


class TestGitHubAdapter:
    """Tests for GitHubAdapter."""
    
    @pytest.fixture
    def github_adapter(self):
        """Create a GitHub adapter for testing."""
        config = AdapterConfig(
            name="github",
            capabilities=[
                "repository.read",
                "pull_request.create",
                "issues.manage",
            ],
            extra={
                "base_url": "https://api.github.com",
                "token_env": "GITHUB_TOKEN",
            },
        )
        return GitHubAdapter(config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, github_adapter):
        """Test adapter initialization."""
        await github_adapter.initialize()
        
        assert github_adapter._initialized is True
        assert github_adapter._base_url == "https://api.github.com"
    
    @pytest.mark.asyncio
    async def test_get_repository(self, github_adapter):
        """Test getting repository information."""
        await github_adapter.initialize()
        
        request = MCPRequest(
            method="repository.get",
            params={"owner": "test-org", "repo": "test-repo"},
        )
        
        response = await github_adapter.execute(request)
        
        assert response.success is True
        assert response.data["owner"] == "test-org"
        assert response.data["repo"] == "test-repo"
    
    @pytest.mark.asyncio
    async def test_create_pull_request(self, github_adapter):
        """Test creating a pull request."""
        await github_adapter.initialize()
        
        request = MCPRequest(
            method="pull_request.create",
            params={
                "owner": "test-org",
                "repo": "test-repo",
                "title": "Test PR",
                "body": "Test description",
                "base": "main",
                "head": "feature",
            },
        )
        
        response = await github_adapter.execute(request)
        
        assert response.success is True
        assert response.data["status"] == "created"
        assert "url" in response.data
    
    @pytest.mark.asyncio
    async def test_list_pull_requests(self, github_adapter):
        """Test listing pull requests."""
        await github_adapter.initialize()
        
        request = MCPRequest(
            method="pull_request.list",
            params={"owner": "test-org", "repo": "test-repo"},
        )
        
        response = await github_adapter.execute(request)
        
        assert response.success is True
        assert isinstance(response.data, list)
    
    @pytest.mark.asyncio
    async def test_review_pull_request(self, github_adapter):
        """Test reviewing a pull request."""
        await github_adapter.initialize()
        
        request = MCPRequest(
            method="pull_request.review",
            params={
                "owner": "test-org",
                "repo": "test-repo",
                "number": 1,
                "event": "APPROVE",
                "body": "LGTM!",
            },
        )
        
        response = await github_adapter.execute(request)
        
        assert response.success is True
        assert response.data["status"] == "submitted"
    
    @pytest.mark.asyncio
    async def test_create_issue(self, github_adapter):
        """Test creating an issue."""
        await github_adapter.initialize()
        
        request = MCPRequest(
            method="issues.create",
            params={
                "owner": "test-org",
                "repo": "test-repo",
                "title": "Test Issue",
                "body": "Issue description",
            },
        )
        
        response = await github_adapter.execute(request)
        
        assert response.success is True
        assert response.data["status"] == "created"
    
    @pytest.mark.asyncio
    async def test_trigger_workflow(self, github_adapter):
        """Test triggering a workflow."""
        await github_adapter.initialize()
        
        request = MCPRequest(
            method="actions.trigger",
            params={
                "owner": "test-org",
                "repo": "test-repo",
                "workflow": "ci.yml",
            },
        )
        
        response = await github_adapter.execute(request)
        
        assert response.success is True
        assert response.data["status"] == "triggered"
    
    @pytest.mark.asyncio
    async def test_unknown_method(self, github_adapter):
        """Test handling unknown method."""
        await github_adapter.initialize()
        
        request = MCPRequest(
            method="unknown.method",
            params={},
        )
        
        response = await github_adapter.execute(request)
        
        assert response.success is False
        assert "Unknown method" in response.error
    
    @pytest.mark.asyncio
    async def test_convenience_methods(self, github_adapter):
        """Test convenience methods."""
        await github_adapter.initialize()
        
        response = await github_adapter.get_repository("test-org", "test-repo")
        
        assert response.success is True
        assert response.data["owner"] == "test-org"
    
    @pytest.mark.asyncio
    async def test_create_pr_convenience(self, github_adapter):
        """Test create PR convenience method."""
        await github_adapter.initialize()
        
        response = await github_adapter.create_pull_request(
            owner="test-org",
            repo="test-repo",
            title="New Feature",
            body="Description",
            base="main",
            head="feature/new",
        )
        
        assert response.success is True
