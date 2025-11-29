"""Configuration utilities for DevOps Brain."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, Field, ValidationError

CONFIG_DEFAULT_PATH = Path("configs/brain.yaml")


class AgentConfig(BaseModel):
    """Describes an agent that can be orchestrated by the brain."""

    name: str
    role: str
    model: str | None = None
    description: str | None = None
    skills: List[str] = Field(default_factory=list)
    routing_tags: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class MCPAdapterConfig(BaseModel):
    """Describes an MCP adapter that agents can call into."""

    name: str
    type: str
    settings: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStepConfig(BaseModel):
    """Single unit of work within a workflow."""

    name: str
    agent: str
    action: str
    adapter: str | None = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expects: List[str] = Field(default_factory=list)


class WorkflowConfig(BaseModel):
    """Workflow definition loaded either inline or from file."""

    name: str
    description: str
    triggers: List[str] = Field(default_factory=list)
    steps: List[WorkflowStepConfig]
    path: str | None = None


class BrainMetadata(BaseModel):
    """Metadata that helps categorize this DevOps Brain deployment."""

    environment: str = "local"
    owner: str | None = None
    mission: str | None = None


class BrainConfig(BaseModel):
    """Top-level DevOps Brain configuration."""

    version: str = "1.0"
    metadata: BrainMetadata = BrainMetadata()
    agents: List[AgentConfig]
    workflows: List[WorkflowConfig]
    mcp_adapters: List[MCPAdapterConfig] = Field(default_factory=list)

    def agent_by_name(self, name: str) -> AgentConfig:
        for agent in self.agents:
            if agent.name == name:
                return agent
        raise KeyError(f"Agent '{name}' is not defined in configuration.")

    def workflow_by_name(self, name: str) -> WorkflowConfig:
        for wf in self.workflows:
            if wf.name == name:
                return wf
        raise KeyError(f"Workflow '{name}' is not defined in configuration.")

    def adapter_by_name(self, name: str) -> MCPAdapterConfig:
        for adapter in self.mcp_adapters:
            if adapter.name == name:
                return adapter
        raise KeyError(f"MCP adapter '{name}' is not defined in configuration.")


@dataclass(slots=True)
class LoadedConfig:
    """Convenience container for config path and parsed model."""

    path: Path
    model: BrainConfig


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _merge_workflow(path: Path, inline_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merges workflow details from referenced YAML file with inline overrides."""

    workflow_path_value = inline_config.get("path")
    if not workflow_path_value:
        return inline_config

    workflow_path = (path.parent / workflow_path_value).resolve()
    file_payload = _load_yaml(workflow_path)

    merged = {**file_payload, **{k: v for k, v in inline_config.items() if k != "path"}}
    merged.setdefault("description", file_payload.get("description", ""))
    merged.setdefault("name", file_payload.get("name"))
    try:
        merged["path"] = str(workflow_path.relative_to(path.parent))
    except ValueError:
        merged["path"] = str(workflow_path)
    return merged


def load_brain_config(path: Path | None = None) -> LoadedConfig:
    """Load and validate a DevOps Brain configuration file."""

    resolved = (path or CONFIG_DEFAULT_PATH).resolve()
    payload = _load_yaml(resolved)
    workflows = [_merge_workflow(resolved, wf) for wf in payload.get("workflows", [])]
    payload["workflows"] = workflows

    try:
        model = BrainConfig.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(f"Invalid configuration in {resolved}: {exc}") from exc

    return LoadedConfig(path=resolved, model=model)
