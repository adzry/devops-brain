"""Agent abstractions for DevOps Brain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from devops_brain.config import AgentConfig, WorkflowStepConfig
from devops_brain.mcp.base import MCPRegistry
from devops_brain.utils.logging import get_logger


@dataclass(slots=True)
class AgentContext:
    """Holds shared state for agents while a workflow executes."""

    workflow_step: WorkflowStepConfig
    objective: str
    artifacts: List[str] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    adapter_registry: MCPRegistry | None = None


@dataclass(slots=True)
class Result:
    """Represents agent output."""

    summary: str
    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    """Base behaviour for all agents."""

    def __init__(self, config: AgentConfig, registry: MCPRegistry | None = None):
        self.config = config
        self.registry = registry
        self.logger = get_logger(f"agent.{config.name}")

    def act(self, action: str, context: AgentContext) -> Result:
        handler_name = f"action_{action.replace('-', '_')}"
        handler = getattr(self, handler_name, None)
        if handler:
            return handler(context)

        self.logger.info("Executing generic action '%s' for step %s", action, context.workflow_step.name)
        return Result(summary=f"Completed action {action}.", success=True, outputs=context.memory)

    def _call_adapter(self, adapter_name: str, action: str, payload: Dict[str, Any]):
        if not self.registry:
            raise RuntimeError("Adapter registry is not available.")
        result = self.registry.execute(adapter_name, action, payload)
        return result.details


class PlannerAgent(BaseAgent):
    """Turns objectives into executable plans."""

    def action_plan(self, context: AgentContext) -> Result:
        steps = [
            f"Clarify requirements for {context.workflow_step.name}",
            "Break work into sub-steps",
            "Share execution playbook with executor agent",
        ]
        self.logger.debug("Planner generated %d steps", len(steps))
        return Result(
            summary=f"Plan ready for {context.workflow_step.name}",
            success=True,
            outputs={"plan": steps, "objective": context.objective},
        )

    def action_refine_plan(self, context: AgentContext) -> Result:
        plan = context.memory.get("plan", [])
        plan.append("Incorporate feedback and update stakeholders")
        return Result(
            summary="Plan refined with stakeholder feedback.",
            success=True,
            outputs={"plan": plan},
        )


class ExecutorAgent(BaseAgent):
    """Executes playbooks by orchestrating MCP adapters."""

    def action_trigger_ci(self, context: AgentContext) -> Result:
        adapter = context.workflow_step.adapter or "github"
        details = self._call_adapter(
            adapter,
            "dispatch_workflow",
            {
                "workflow": context.workflow_step.inputs.get("workflow", "release.yml"),
                "repo": context.workflow_step.inputs.get("repo"),
                "inputs": context.workflow_step.inputs.get("inputs", {}),
            },
        )
        return Result(summary="CI pipeline triggered.", success=True, outputs=details)

    def action_deploy(self, context: AgentContext) -> Result:
        adapter = context.workflow_step.adapter or "kubernetes"
        details = self._call_adapter(
            adapter,
            "apply_manifest",
            {
                "manifest": context.workflow_step.inputs.get("manifest", "deployment.yaml"),
                "namespace": context.workflow_step.inputs.get("namespace", "default"),
            },
        )
        return Result(summary="Deployment applied.", success=True, outputs=details)


class ObserverAgent(BaseAgent):
    """Validates outcomes and propagates signals."""

    def action_verify(self, context: AgentContext) -> Result:
        adapter = context.workflow_step.adapter or "ci"
        details = self._call_adapter(
            adapter,
            "fetch_status",
            {
                "pipeline": context.workflow_step.inputs.get("pipeline", "release"),
                "status": context.workflow_step.inputs.get("status", "green"),
            },
        )
        return Result(summary="Verification complete.", success=True, outputs=details)

    def action_report(self, context: AgentContext) -> Result:
        adapter = context.workflow_step.adapter or "github"
        details = self._call_adapter(
            adapter,
            "open_issue",
            {
                "title": context.workflow_step.inputs.get("title", "Automation report"),
                "body": context.workflow_step.inputs.get("body", "See attached logs."),
            },
        )
        return Result(summary="Report shared with stakeholders.", success=True, outputs=details)
