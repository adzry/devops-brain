from __future__ import annotations

import yaml
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any

from .logging_utils import setup_logger
from .models import BrainConfig, BrainMetadata, AgentConfig


class DevOpsBrain:
    """
    Orchestrator that loads Brain config and workflows, and can execute simple workflows.
    This is intentionally conservative but production-ready in structure.
    """

    def __init__(self, brain_config_path: str = "configs/brain.yaml") -> None:
        self.logger = setup_logger()
        self.config_path = Path(brain_config_path)
        self.config = self._load_config()
        self.workflows: Dict[str, Dict[str, Any]] = self._load_workflows()

    def _load_config(self) -> BrainConfig:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Brain config not found: {self.config_path}")
        data = yaml.safe_load(self.config_path.read_text())

        meta_raw = data.get("metadata", {})
        metadata = BrainMetadata(
            name=meta_raw.get("name", "devops-brain"),
            owner=meta_raw.get("owner", "unknown"),
            description=meta_raw.get("description", ""),
        )

        agents_map: Dict[str, AgentConfig] = {}
        for agent in data.get("agents", []):
            cfg = AgentConfig(
                name=agent["name"],
                role=agent["role"],
                kind=agent["kind"],
                description=agent.get("description", ""),
                write_access=bool(agent.get("write_access", False)),
                domains=list(agent.get("domains", [])),
            )
            agents_map[cfg.name] = cfg

        mcp = data.get("mcp", {})

        brain_config = BrainConfig(metadata=metadata, agents=agents_map, mcp=mcp)
        self.logger.info("Loaded Brain config: %s", asdict(brain_config.metadata))
        self.logger.info("Agents: %s", list(brain_config.agents.keys()))
        return brain_config

    def _load_workflows(self) -> Dict[str, Dict[str, Any]]:
        wf_dir = Path("configs/workflows")
        workflows: Dict[str, Dict[str, Any]] = {}
        if not wf_dir.exists():
            self.logger.warning("Workflow directory missing: %s", wf_dir)
            return workflows

        for path in wf_dir.glob("*.yaml"):
            wf = yaml.safe_load(path.read_text())
            name = wf.get("name", path.stem)
            workflows[name] = wf
        self.logger.info("Loaded workflows: %s", list(workflows.keys()))
        return workflows

    # --- Workflow execution ---

    def run_workflow(self, name: str) -> None:
        wf = self.workflows.get(name)
        if not wf:
            raise ValueError(f"Workflow not found: {name}")
        self.logger.info("Running workflow: %s", name)
        for step in wf.get("steps", []):
            self._run_step(step)
        self.logger.info("Workflow completed: %s", name)

    def _run_step(self, step: Dict[str, Any]) -> None:
        step_type = step.get("type")
        if step_type == "internal":
            self._run_internal_step(step)
        elif step_type == "agent":
            self._run_agent_step(step)
        elif step_type == "mcp":
            self._run_mcp_step(step)
        else:
            self.logger.warning("Unknown step type: %s", step_type)

    def _run_internal_step(self, step: Dict[str, Any]) -> None:
        action = step.get("action")
        params = step.get("params", {})
        if action == "ensure_directories":
            paths = params.get("paths", [])
            for p in paths:
                path = Path(p)
                path.mkdir(parents=True, exist_ok=True)
                self.logger.info("Ensured directory: %s", path)
        elif action == "log_message":
            level = params.get("level", "info").lower()
            msg = params.get("message", "")
            getattr(self.logger, level, self.logger.info)(msg)
        else:
            self.logger.warning("Unknown internal action: %s", action)

    def _run_agent_step(self, step: Dict[str, Any]) -> None:
        agent_name = step.get("agent")
        topic = step.get("topic", "")
        agent_cfg = self.config.agents.get(agent_name)
        if not agent_cfg:
            self.logger.warning("Agent not found: %s", agent_name)
            return
        self.logger.info(
            "Delegating to agent '%s' (%s) on topic: %s",
            agent_cfg.name,
            agent_cfg.role,
            topic,
        )
        # In a real system, this is where Cursor/LLM agent would be invoked.

    def _run_mcp_step(self, step: Dict[str, Any]) -> None:
        server = step.get("server")
        tool = step.get("tool")
        params = step.get("params", {})
        self.logger.info(
            "MCP step: server=%s tool=%s params=%s (wire up MCP here)", server, tool, params
        )
        # In Cursor, this would call the MCP tool. From plain Python, this is a stub.
