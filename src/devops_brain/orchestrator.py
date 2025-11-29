"""DevOps Brain orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from devops_brain.agents import BaseAgent, ExecutorAgent, ObserverAgent, PlannerAgent
from devops_brain.config import BrainConfig, load_brain_config
from devops_brain.mcp import MCPRegistry
from devops_brain.mcp.adapters import CIAdapter, GitHubAdapter, KubernetesAdapter
from devops_brain.utils.logging import get_logger
from devops_brain.workflows import Workflow, WorkflowResult

AGENT_TYPE_MAP = {
    "planner": PlannerAgent,
    "executor": ExecutorAgent,
    "observer": ObserverAgent,
}

ADAPTER_TYPE_MAP = {
    "github": GitHubAdapter,
    "kubernetes": KubernetesAdapter,
    "ci": CIAdapter,
}


class DevOpsBrain:
    """Wires agents, adapters, and workflows into a single system."""

    def __init__(self, config_path: Optional[str] = None):
        resolved_path = Path(config_path).expanduser() if config_path else None
        loaded = load_brain_config(resolved_path)
        self.config_path = loaded.path
        self.config: BrainConfig = loaded.model
        self.logger = get_logger("devops-brain")
        self.registry = MCPRegistry()
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, Workflow] = {}
        self._bootstrap()

    def _bootstrap(self) -> None:
        self.logger.info("Initializing DevOps Brain with config at %s", self.config_path)
        self._register_adapters()
        self._register_agents()
        self._register_workflows()

    def _register_adapters(self) -> None:
        for adapter_config in self.config.mcp_adapters:
            adapter_cls = ADAPTER_TYPE_MAP.get(adapter_config.type)
            if not adapter_cls:
                self.logger.warning(
                    "Adapter type '%s' is not recognized. Skipping.", adapter_config.type
                )
                continue
            adapter = adapter_cls(adapter_config)
            self.registry.register(adapter)
            self.logger.debug("Registered adapter %s", adapter_config.name)

    def _register_agents(self) -> None:
        for agent_config in self.config.agents:
            agent_cls = AGENT_TYPE_MAP.get(agent_config.role, PlannerAgent)
            agent = agent_cls(agent_config, self.registry)
            self.agents[agent_config.name] = agent
            self.logger.debug("Registered agent %s (%s)", agent_config.name, agent_config.role)

    def _register_workflows(self) -> None:
        for workflow_config in self.config.workflows:
            workflow = Workflow(workflow_config)
            self.workflows[workflow.name] = workflow
            self.logger.debug("Registered workflow %s", workflow.name)

    def get_agent(self, name: str) -> BaseAgent:
        if name not in self.agents:
            raise KeyError(f"Agent '{name}' is not available.")
        return self.agents[name]

    def run_workflow(self, workflow_name: str, objective: str) -> WorkflowResult:
        if workflow_name not in self.workflows:
            raise KeyError(f"Workflow '{workflow_name}' is not registered.")
        workflow = self.workflows[workflow_name]
        self.logger.info("Starting workflow '%s' for objective '%s'", workflow_name, objective)
        return workflow.run(self, objective)

    def list_agents(self) -> Dict[str, str]:
        return {name: agent.config.role for name, agent in self.agents.items()}

    def list_workflows(self) -> Dict[str, str]:
        return {name: wf.config.description for name, wf in self.workflows.items()}

    def list_adapters(self) -> Dict[str, str]:
        return self.registry.info()
