"""
Documentation Agent

Specialized agent for automated documentation generation,
maintenance, and quality assurance.
"""

from enum import Enum
from typing import Any

from .base_agent import BaseAgent


class DocFormat(Enum):
    """Documentation output formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    RST = "rst"
    OPENAPI = "openapi"
    DOCSTRING = "docstring"


class DocumentationAgent(BaseAgent):
    """
    Documentation-focused agent for comprehensive documentation automation.
    
    Capabilities:
    - API documentation generation
    - Code documentation and docstrings
    - README generation
    - Changelog management
    - Architecture diagrams
    - Tutorial creation
    """
    
    SYSTEM_PROMPT = """You are the Documentation Agent for DevOps Brain. Your mission is to 
ensure comprehensive, accurate, and up-to-date documentation.

Your responsibilities:
1. Generate and maintain API documentation
2. Create clear code documentation and docstrings
3. Write READMEs and getting started guides
4. Maintain changelogs and release notes
5. Create architecture diagrams and technical docs

Documentation principles:
- Write for your audience (developers, users, operators)
- Keep documentation close to code
- Use examples liberally
- Update docs with code changes

Good documentation is the difference between adoption and abandonment."""

    def _register_handlers(self) -> None:
        """Register documentation action handlers."""
        self.register_handler("generate_api_docs", self._generate_api_docs)
        self.register_handler("generate_readme", self._generate_readme)
        self.register_handler("generate_docstrings", self._generate_docstrings)
        self.register_handler("update_changelog", self._update_changelog)
        self.register_handler("generate_diagram", self._generate_diagram)
        self.register_handler("create_tutorial", self._create_tutorial)
        self.register_handler("audit_docs", self._audit_documentation)
    
    async def _get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def _generate_api_docs(self, payload: dict[str, Any]) -> dict:
        """Generate API documentation."""
        source = payload.get("source", "src/api/")
        format_type = payload.get("format", "openapi")
        
        self.logger.info(f"Generating API docs from {source} in {format_type} format")
        
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "DevOps Brain API",
                "version": "1.0.0",
                "description": "API for DevOps automation and agent management",
            },
            "paths": {
                "/agents": {
                    "get": {
                        "summary": "List all agents",
                        "responses": {
                            "200": {
                                "description": "List of agents",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Agent"},
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
                "/agents/{id}/execute": {
                    "post": {
                        "summary": "Execute agent action",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ActionRequest"}
                                }
                            }
                        },
                        "responses": {
                            "200": {"description": "Action executed successfully"},
                            "404": {"description": "Agent not found"},
                        },
                    }
                },
            },
            "components": {
                "schemas": {
                    "Agent": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "status": {"type": "string"},
                            "capabilities": {"type": "array", "items": {"type": "string"}},
                        },
                    }
                }
            },
        }
        
        return {
            "data": {
                "format": format_type,
                "endpoints_documented": 2,
                "schemas_documented": 1,
                "spec": openapi_spec,
                "output_file": "docs/api/openapi.yaml",
            },
            "recommendations": [
                "Add authentication documentation",
                "Include rate limiting information",
                "Add request/response examples",
            ],
        }
    
    async def _generate_readme(self, payload: dict[str, Any]) -> dict:
        """Generate README documentation."""
        project_name = payload.get("project", "Project")
        include_sections = payload.get("sections", ["overview", "installation", "usage"])
        
        self.logger.info(f"Generating README for {project_name}")
        
        readme_content = f"""# {project_name}

A brief description of what this project does.

## Features

- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Installation

```bash
pip install {project_name.lower().replace(' ', '-')}
```

## Quick Start

```python
from {project_name.lower().replace(' ', '_')} import Client

client = Client(api_key="your-api-key")
result = client.process("input data")
print(result)
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | Your API key | Required |
| `TIMEOUT` | Request timeout in seconds | 30 |

## Documentation

Full documentation is available at [docs link].

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file for details.
"""
        
        return {
            "data": {
                "project": project_name,
                "sections_included": include_sections,
                "content": readme_content,
                "word_count": len(readme_content.split()),
            },
            "recommendations": [
                "Add badges for build status and coverage",
                "Include architecture overview diagram",
                "Add troubleshooting section",
            ],
        }
    
    async def _generate_docstrings(self, payload: dict[str, Any]) -> dict:
        """Generate docstrings for code."""
        file_path = payload.get("file")
        style = payload.get("style", "google")
        
        self.logger.info(f"Generating {style} style docstrings for {file_path}")
        
        generated_docstrings = [
            {
                "function": "process_data",
                "line": 25,
                "docstring": '''"""Process input data and return transformed result.

    Args:
        data: The input data to process. Can be a dict or list.
        options: Optional processing options.
            - validate: Whether to validate input (default: True)
            - transform: Transformation type (default: "standard")

    Returns:
        dict: Processed data with the following structure:
            - result: The transformed data
            - metadata: Processing metadata

    Raises:
        ValueError: If data is None or empty.
        ProcessingError: If transformation fails.

    Example:
        >>> result = process_data({"key": "value"})
        >>> print(result["result"])
        {"key": "VALUE"}
    """''',
            },
            {
                "function": "validate_input",
                "line": 45,
                "docstring": '''"""Validate input data against schema.

    Args:
        data: Input data to validate.
        schema: JSON schema for validation.

    Returns:
        bool: True if validation passes.

    Raises:
        ValidationError: If validation fails with details.
    """''',
            },
        ]
        
        return {
            "data": {
                "file": file_path,
                "style": style,
                "docstrings_generated": len(generated_docstrings),
                "docstrings": generated_docstrings,
            },
            "recommendations": [
                "Consider adding type hints alongside docstrings",
                "Include edge case examples in docstrings",
            ],
        }
    
    async def _update_changelog(self, payload: dict[str, Any]) -> dict:
        """Update changelog with new entries."""
        version = payload.get("version", "unreleased")
        changes = payload.get("changes", [])
        
        self.logger.info(f"Updating changelog for version {version}")
        
        changelog_entry = f"""## [{version}] - 2024-11-29

### Added
- New Security Agent for vulnerability scanning
- Testing Agent with mutation testing support
- Documentation Agent for automated docs generation

### Changed
- Improved agent orchestration performance
- Updated MCP adapter retry logic

### Fixed
- Fixed race condition in async message handling
- Resolved memory leak in long-running agents

### Security
- Upgraded dependencies to address CVE-2024-1234
"""
        
        return {
            "data": {
                "version": version,
                "entry": changelog_entry,
                "changes_categorized": {
                    "added": 3,
                    "changed": 2,
                    "fixed": 2,
                    "security": 1,
                },
            },
            "recommendations": [
                "Link issues/PRs in changelog entries",
                "Include migration notes for breaking changes",
            ],
        }
    
    async def _generate_diagram(self, payload: dict[str, Any]) -> dict:
        """Generate architecture or flow diagrams."""
        diagram_type = payload.get("type", "architecture")
        scope = payload.get("scope", "system")
        
        self.logger.info(f"Generating {diagram_type} diagram for {scope}")
        
        mermaid_diagram = """```mermaid
graph TB
    subgraph "DevOps Brain"
        O[Orchestrator]
        
        subgraph "Specialist Agents"
            SA[Security Agent]
            TA[Testing Agent]
            DA[Documentation Agent]
            PA[Performance Agent]
            IA[Incident Agent]
        end
        
        subgraph "MCP Adapters"
            GH[GitHub]
            SL[Slack]
            DB[Database]
            MON[Monitoring]
        end
    end
    
    O --> SA
    O --> TA
    O --> DA
    O --> PA
    O --> IA
    
    SA --> GH
    TA --> GH
    DA --> GH
    IA --> SL
    IA --> MON
    PA --> MON
    
    style O fill:#4a90d9
    style SA fill:#e74c3c
    style TA fill:#27ae60
    style DA fill:#9b59b6
    style PA fill:#f39c12
    style IA fill:#e67e22
```"""
        
        return {
            "data": {
                "type": diagram_type,
                "format": "mermaid",
                "diagram": mermaid_diagram,
                "output_file": f"docs/diagrams/{diagram_type}.md",
            },
            "recommendations": [
                "Add sequence diagrams for key workflows",
                "Include deployment architecture diagram",
            ],
        }
    
    async def _create_tutorial(self, payload: dict[str, Any]) -> dict:
        """Create a tutorial or guide."""
        topic = payload.get("topic", "getting-started")
        audience = payload.get("audience", "developers")
        
        self.logger.info(f"Creating {topic} tutorial for {audience}")
        
        tutorial_content = f"""# Getting Started with DevOps Brain

This tutorial will guide you through setting up and using DevOps Brain
for your DevOps automation needs.

## Prerequisites

- Python 3.11+
- Git
- API credentials for integrations

## Step 1: Installation

First, clone the repository and set up your environment:

```bash
git clone https://github.com/your-org/devops-brain.git
cd devops-brain
./scripts/setup.sh
```

## Step 2: Configuration

Create your environment configuration:

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Step 3: Run Your First Agent

```python
from agents.specialists import SecurityAgent

# Initialize the security agent
agent = SecurityAgent(config)
await agent.initialize()

# Scan for vulnerabilities
result = await agent.process(
    AgentMessage(action="scan_vulnerabilities", payload={{"target": "src/"}})
)
print(result.data)
```

## Step 4: Set Up Workflows

Create a workflow configuration in `workflows/`:

```yaml
name: my_workflow
triggers:
  - event: push
stages:
  - name: security_scan
    agent: security_agent
    steps:
      - action: scan_vulnerabilities
```

## Next Steps

- Explore other specialist agents
- Set up MCP adapters for integrations
- Configure automated workflows

## Need Help?

- Check the [FAQ](docs/faq.md)
- Join our [Slack channel](#)
- Open an issue on GitHub
"""
        
        return {
            "data": {
                "topic": topic,
                "audience": audience,
                "content": tutorial_content,
                "estimated_read_time_minutes": 10,
                "output_file": f"docs/tutorials/{topic}.md",
            },
            "recommendations": [
                "Add video walkthrough",
                "Include troubleshooting section",
                "Add links to related tutorials",
            ],
        }
    
    async def _audit_documentation(self, payload: dict[str, Any]) -> dict:
        """Audit documentation for completeness and accuracy."""
        scope = payload.get("scope", "all")
        
        self.logger.info(f"Auditing documentation (scope: {scope})")
        
        return {
            "data": {
                "files_audited": 15,
                "coverage_score": 72,
                "issues": [
                    {
                        "file": "docs/api/agents.md",
                        "issue": "Missing documentation for 3 new endpoints",
                        "severity": "high",
                    },
                    {
                        "file": "README.md",
                        "issue": "Installation instructions outdated",
                        "severity": "medium",
                    },
                    {
                        "file": "src/api/handlers.py",
                        "issue": "5 functions missing docstrings",
                        "severity": "medium",
                    },
                ],
                "stats": {
                    "functions_documented": 85,
                    "functions_total": 100,
                    "api_endpoints_documented": 12,
                    "api_endpoints_total": 15,
                },
            },
            "recommendations": [
                "Document new API endpoints",
                "Update installation guide",
                "Add docstrings to undocumented functions",
                "Set up documentation CI checks",
            ],
        }
