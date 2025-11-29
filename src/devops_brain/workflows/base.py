"""Workflow execution primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from devops_brain.agents import AgentContext, Result
from devops_brain.config import WorkflowConfig


@dataclass(slots=True)
class WorkflowResult:
    """Aggregated workflow execution data."""

    name: str
    success: bool
    steps: List[Result] = field(default_factory=list)
    shared_state: Dict[str, Any] = field(default_factory=dict)


class Workflow:
    """Executes each configured step in sequence."""

    def __init__(self, config: WorkflowConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    def run(
        self, orchestrator, objective: str, shared_memory: Dict[str, Any] | None = None
    ) -> WorkflowResult:
        state = shared_memory or {}
        results: List[Result] = []
        overall_success = True

        for step in self.config.steps:
            agent = orchestrator.get_agent(step.agent)
            context = AgentContext(
                workflow_step=step,
                objective=objective,
                memory=state,
                adapter_registry=orchestrator.registry,
            )
            orchestrator.logger.info("Running step '%s' with agent '%s'", step.name, step.agent)
            result = agent.act(step.action, context)
            results.append(result)
            state.update(result.outputs)
            overall_success = overall_success and result.success

        return WorkflowResult(name=self.name, success=overall_success, steps=results, shared_state=state)
