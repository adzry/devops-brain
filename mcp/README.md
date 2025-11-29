# MCP Adapters

Model Context Protocol (MCP) adapters for integrating DevOps Brain with external services.

## Available Adapters

| Adapter | Description | Status |
|---------|-------------|--------|
| GitHub | Repository operations, PRs, issues | ✅ Ready |
| Slack | Notifications and messaging | ✅ Ready |
| Database | Database query and management | ✅ Ready |
| Monitoring | Metrics and alerting services | ✅ Ready |

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  DevOps Brain   │────▶│ MCP Adapters │────▶│ External Service│
│    (Agents)     │◀────│   (Bridge)   │◀────│    (API)        │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

## Configuration

Adapters are configured via `mcp_config.yaml` and can be extended by adding
new adapter modules to the `adapters/` directory.

## Usage

```python
from mcp.adapters import GitHubAdapter

adapter = GitHubAdapter(config)
await adapter.create_pull_request(
    title="Feature: Add new functionality",
    body="Description of changes",
    base="main",
    head="feature/branch"
)
```
