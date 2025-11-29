# DevOps Brain 🧠

A comprehensive automation platform for bootstrapping Cursor cloud agents, orchestrating automation workflows, and integrating with external services via MCP adapters.

## Overview

DevOps Brain provides:

- **Cloud Agents** - Configurable AI agents for code review, deployment, and orchestration
- **Automation Workflows** - YAML-defined pipelines for CI/CD, PR automation, and deployments
- **MCP Adapters** - Model Context Protocol integrations with GitHub, Slack, databases, and monitoring services

## Project Structure

```
devops-brain/
├── agents/                 # Cloud agent configurations
│   ├── agent_config.yaml   # Agent definitions and capabilities
│   └── README.md
├── workflows/              # Automation workflow definitions
│   ├── pr_workflow.yaml    # Pull request automation
│   ├── ci_workflow.yaml    # Continuous integration
│   ├── deploy_workflow.yaml# Deployment pipelines
│   └── README.md
├── mcp/                    # MCP adapters
│   ├── adapters/           # Adapter implementations
│   │   ├── base_adapter.py
│   │   ├── github_adapter.py
│   │   ├── slack_adapter.py
│   │   ├── database_adapter.py
│   │   └── monitoring_adapter.py
│   ├── mcp_config.yaml     # Adapter configuration
│   └── README.md
├── config/                 # Global configuration
│   └── settings.yaml
├── scripts/                # Utility scripts
│   └── setup.sh
├── requirements.txt        # Python dependencies
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd devops-brain
   ```

2. Run the setup script:
   ```bash
   ./scripts/setup.sh
   ```

3. Configure your environment:
   ```bash
   # Edit .env with your credentials
   vi .env
   ```

4. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub personal access token | Yes |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `DATADOG_API_KEY` | Datadog API key | Optional |

### Agent Configuration

Agents are defined in `agents/agent_config.yaml`:

```yaml
agents:
  root_agent:
    name: "Root Agent"
    model: "gpt-5.1-codex-high"
    capabilities:
      - code_generation
      - workflow_orchestration
```

### Workflow Configuration

Workflows are YAML files in the `workflows/` directory:

```yaml
name: my_workflow
triggers:
  - event: push
stages:
  - name: build
    steps:
      - action: run_command
        command: "npm run build"
```

## MCP Adapters

### GitHub Adapter

```python
from mcp.adapters import GitHubAdapter

adapter = GitHubAdapter(config)
await adapter.create_pull_request(
    owner="org",
    repo="repo",
    title="Feature: New functionality",
    body="Description",
    base="main",
    head="feature/branch"
)
```

### Slack Adapter

```python
from mcp.adapters import SlackAdapter

adapter = SlackAdapter(config)
await adapter.send_deployment_notification(
    environment="production",
    version="v1.2.3",
    status="success"
)
```

### Database Adapter

```python
from mcp.adapters import DatabaseAdapter

adapter = DatabaseAdapter(config)
result = await adapter.select("SELECT * FROM users LIMIT 10")
```

### Monitoring Adapter

```python
from mcp.adapters import MonitoringAdapter

adapter = MonitoringAdapter(config)
await adapter.send_deployment_event(
    version="v1.2.3",
    environment="production",
    status="success"
)
```

## Development

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

### Type Checking

```bash
mypy .
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DevOps Brain                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Root Agent  │  │ Code Review │  │ Deployment  │         │
│  │             │  │   Agent     │  │   Agent     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                   Workflow Engine                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PR Workflow │  │ CI Workflow │  │   Deploy    │         │
│  │             │  │             │  │  Workflow   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    MCP Adapters                             │
│  ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────────┐      │
│  │ GitHub │  │ Slack  │  │ Database │  │ Monitoring │      │
│  └────────┘  └────────┘  └──────────┘  └────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

All changes must be described using Pull Requests as per project guidelines.
