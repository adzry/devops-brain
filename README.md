# DevOps Brain 🧠

A comprehensive AI-powered DevOps automation platform featuring cloud agents, automation workflows, MCP adapters, and a full-stack runtime.

## Features

- **🤖 Specialist Agents** - AI agents for security, testing, documentation, performance, incidents, database, and infrastructure
- **⚙️ Orchestrator** - Central coordinator for task routing and agent management
- **🔌 MCP Adapters** - Integrations with GitHub, Slack, databases, and monitoring services
- **🚀 REST API** - FastAPI-based API for external access
- **💻 CLI** - Command-line interface for local interactions
- **🐳 Docker** - Containerized deployment with docker-compose
- **☸️ Kubernetes** - Production-ready K8s manifests with HPA, PDB, and Ingress

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- kubectl (for Kubernetes deployment)

### Local Development

```bash
# Clone and setup
git clone <repository-url>
cd devops-brain
./scripts/setup.sh

# Activate virtual environment
source .venv/bin/activate

# Run the API server
uvicorn src.api.main:app --reload

# Or use the CLI
python -m src.cli.main --help
```

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -k docker/kubernetes/

# Check status
kubectl get pods -n devops-brain

# Port forward for local access
kubectl port-forward -n devops-brain svc/devops-brain-api 8000:80
```

## Project Structure

```
devops-brain/
├── agents/                     # Cloud agent configurations
│   ├── specialists/            # Agent implementations
│   │   ├── security_agent.py
│   │   ├── testing_agent.py
│   │   ├── documentation_agent.py
│   │   ├── performance_agent.py
│   │   ├── incident_response_agent.py
│   │   ├── database_agent.py
│   │   └── infrastructure_agent.py
│   └── prompts/                # System prompts
├── src/
│   ├── core/                   # Core components
│   │   ├── orchestrator.py     # Agent orchestrator
│   │   └── message_queue.py    # Priority message queue
│   ├── api/                    # FastAPI application
│   │   ├── main.py
│   │   └── routes/
│   └── cli/                    # CLI application
│       └── main.py
├── mcp/                        # MCP adapters
│   └── adapters/
├── workflows/                  # Automation workflows
├── tests/                      # Test suite
├── docker/                     # Docker configurations
│   ├── kubernetes/             # K8s manifests
│   ├── postgres/
│   └── prometheus/
├── .github/workflows/          # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/health/live` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe |
| `/metrics` | GET | Prometheus metrics |
| `/api/v1/agents` | GET | List agents |
| `/api/v1/agents/{name}` | GET | Get agent info |
| `/api/v1/agents/{name}/execute` | POST | Execute agent action |
| `/api/v1/tasks` | GET | List tasks |
| `/api/v1/tasks/submit` | POST | Submit async task |
| `/api/v1/tasks/execute` | POST | Execute sync task |
| `/api/v1/execute` | POST | Quick task execution |

## CLI Commands

```bash
# Check status
devops-brain status

# Execute an action
devops-brain execute scan_vulnerabilities -p '{"target": "src/"}'

# List agents
devops-brain agents list

# Run security scan
devops-brain scan security --target src/

# Generate tests
devops-brain test generate src/api.py

# Analyze infrastructure costs
devops-brain infra costs --range 30d
```

## Specialist Agents

| Agent | Capabilities |
|-------|-------------|
| **Security Agent** | Vulnerability scanning, secrets detection, compliance checking, threat modeling |
| **Testing Agent** | Test generation, execution, coverage analysis, mutation testing |
| **Documentation Agent** | API docs, README generation, changelog, diagrams |
| **Performance Agent** | Profiling, bottleneck detection, load testing, caching strategies |
| **Incident Response Agent** | Triage, root cause analysis, runbook execution, post-mortems |
| **Database Agent** | Schema design, migrations, query optimization, backups |
| **Infrastructure Agent** | Terraform, Kubernetes, cost optimization, drift detection |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | development |
| `LOG_LEVEL` | Logging level | INFO |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `GITHUB_TOKEN` | GitHub API token | - |
| `SLACK_BOT_TOKEN` | Slack bot token | - |

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov=agents --cov-report=html

# Run specific tests
pytest tests/agents/test_security_agent.py -v
```

### Linting

```bash
# Check code
ruff check .

# Format code
ruff format .

# Type checking
mypy src/ agents/
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DevOps Brain                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   CLI       │    │  REST API   │    │  Webhooks   │             │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘             │
│         │                  │                   │                    │
│         └──────────────────┼───────────────────┘                    │
│                            ▼                                        │
│                    ┌───────────────┐                                │
│                    │  Orchestrator │                                │
│                    └───────┬───────┘                                │
│                            │                                        │
│         ┌──────────────────┼──────────────────┐                    │
│         ▼                  ▼                  ▼                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │
│  │  Security   │   │   Testing   │   │    Docs     │   ...        │
│  │   Agent     │   │   Agent     │   │   Agent     │              │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘              │
│         │                  │                  │                    │
│         └──────────────────┼──────────────────┘                    │
│                            ▼                                        │
│                    ┌───────────────┐                                │
│                    │ MCP Adapters  │                                │
│                    └───────┬───────┘                                │
│                            │                                        │
│         ┌──────────────────┼──────────────────┐                    │
│         ▼                  ▼                  ▼                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │
│  │   GitHub    │   │   Slack     │   │  Monitoring │              │
│  └─────────────┘   └─────────────┘   └─────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Submit a pull request

All changes must be described using Pull Requests as per project guidelines.
