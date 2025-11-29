# Cloud Agents

This directory contains configuration and implementations for DevOps Brain cloud agents.

## Overview

DevOps Brain uses a multi-agent architecture where specialized agents handle specific domains. The Root Agent orchestrates these specialists to complete complex DevOps tasks.

## Agent Registry

| Agent | Type | Description | Priority |
|-------|------|-------------|----------|
| Root Agent | Orchestrator | Primary task coordination | 1 |
| Security Agent | Specialist | Vulnerability scanning & compliance | 1 |
| Testing Agent | Specialist | Test generation & coverage analysis | 2 |
| Documentation Agent | Specialist | Automated documentation | 3 |
| Performance Agent | Specialist | Profiling & optimization | 2 |
| Incident Response Agent | Specialist | Production incident handling | 1 |
| Database Agent | Specialist | Database operations & optimization | 2 |
| Infrastructure Agent | Specialist | IaC & cloud management | 2 |

## Directory Structure

```
agents/
├── agent_config.yaml      # Agent configurations and capabilities
├── README.md              # This file
├── prompts/               # System prompts for each agent
│   ├── root_agent.md
│   ├── security_agent.md
│   ├── testing_agent.md
│   ├── documentation_agent.md
│   └── incident_response_agent.md
└── specialists/           # Agent implementations
    ├── __init__.py
    ├── base_agent.py      # Base class for all agents
    ├── security_agent.py
    ├── testing_agent.py
    ├── documentation_agent.py
    ├── performance_agent.py
    ├── incident_response_agent.py
    ├── database_agent.py
    └── infrastructure_agent.py
```

## Usage

### Initializing an Agent

```python
from agents.specialists import SecurityAgent, AgentConfig

config = AgentConfig(
    name="security_agent",
    agent_type="specialist",
    model="gpt-5.1-codex-high",
    capabilities=[
        "vulnerability_scanning",
        "secrets_detection",
        "compliance_checking",
    ],
)

agent = SecurityAgent(config)
await agent.initialize()
```

### Processing Messages

```python
from agents.specialists import AgentMessage

message = AgentMessage(
    action="scan_vulnerabilities",
    payload={"target": "src/"},
)

response = await agent.process(message)
print(response.data)
```

### Inter-Agent Communication

```python
# Delegate from one agent to another
response = await root_agent.delegate_task(
    agent_name="testing_agent",
    task="generate_tests",
    context={"file": "src/api/handlers.py"},
)
```

## Agent Capabilities

### Security Agent
- `vulnerability_scanning` - Scan code for security flaws
- `dependency_audit` - Check dependencies for CVEs
- `secrets_detection` - Find exposed credentials
- `compliance_checking` - Validate against security frameworks
- `threat_modeling` - STRIDE-based threat analysis

### Testing Agent
- `test_generation` - Generate tests for code
- `test_execution` - Run test suites
- `coverage_analysis` - Analyze test coverage
- `mutation_testing` - Assess test quality
- `flaky_test_detection` - Identify unreliable tests

### Documentation Agent
- `api_documentation` - Generate OpenAPI/Swagger docs
- `code_documentation` - Create docstrings
- `readme_generation` - Generate README files
- `changelog_management` - Maintain changelogs
- `diagram_generation` - Create architecture diagrams

### Performance Agent
- `performance_profiling` - Profile application performance
- `bottleneck_detection` - Identify performance issues
- `optimization_suggestions` - Recommend improvements
- `load_testing` - Orchestrate load tests
- `memory_analysis` - Analyze memory usage

### Incident Response Agent
- `incident_triage` - Classify and prioritize incidents
- `root_cause_analysis` - Determine incident causes
- `log_analysis` - Analyze logs for issues
- `runbook_execution` - Execute remediation steps
- `post_mortem_generation` - Generate post-mortems

### Database Agent
- `schema_design` - Design database schemas
- `migration_generation` - Create migrations
- `query_optimization` - Optimize SQL queries
- `index_recommendations` - Suggest indexes
- `backup_management` - Plan backup strategies

### Infrastructure Agent
- `terraform_management` - Generate and manage Terraform
- `kubernetes_orchestration` - Manage K8s deployments
- `cost_optimization` - Analyze and reduce costs
- `drift_detection` - Detect infrastructure drift
- `disaster_recovery` - Plan DR strategies

## Configuration

Agents are configured in `agent_config.yaml`:

```yaml
agents:
  security_agent:
    name: "Security Agent"
    type: "specialist"
    model: "gpt-5.1-codex-high"
    capabilities:
      - vulnerability_scanning
      - secrets_detection
    settings:
      scan_depth: "deep"
      severity_threshold: "medium"
```

## Extending Agents

To create a new specialist agent:

1. Create a new file in `specialists/`
2. Extend `BaseAgent` class
3. Implement `_register_handlers()` and `_get_system_prompt()`
4. Add agent configuration to `agent_config.yaml`
5. Create system prompt in `prompts/`

```python
from .base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def _register_handlers(self) -> None:
        self.register_handler("my_action", self._my_action_handler)
    
    async def _get_system_prompt(self) -> str:
        return "You are a custom agent..."
    
    async def _my_action_handler(self, payload: dict) -> dict:
        # Implementation
        return {"data": {...}}
```
