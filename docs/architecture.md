# DevOps Brain Architecture

## Overview

The DevOps Brain couples three primitive layers:

1. **Agents** – persona-focused reasoners that interpret workflow steps and decide what
   to do next. A planner provides strategy, an executor drives infrastructure change,
   and an observer validates outcomes and communicates back to humans or tooling.
2. **MCP adapters** – thin drivers responsible for bridging the brain with external
   systems (GitHub Actions, Kubernetes, CI, etc.). Adapters expose a uniform
   `execute(action, payload)` contract and hide transport/authentication details.
3. **Workflows** – declarative YAML step sets. Each step references an agent, action,
   optional adapter, and typed inputs. Workflows are converted into executable
   `Workflow` objects by the orchestrator.

```
┌────────────┐     ┌──────────────┐     ┌─────────────┐
│ Workflows  │ ──▶ │ Orchestrator │ ──▶ │ MCP Registry│
└────────────┘     └──────┬───────┘     └────┬────────┘
                          │                 │
                    ┌─────▼────┐      ┌─────▼────┐
                    │ Agents   │      │ Adapters │
                    └──────────┘      └──────────┘
```

## Component responsibilities

- `devops_brain.config` – loads `configs/brain.yaml`, merges referenced workflow files,
  and exposes friendly getters for agents/adapters/workflows.
- `devops_brain.orchestrator` – bootstraps adapters, agents, and workflows; offers
  `run_workflow()`, `list_*()` helpers, and instrumentation hooks.
- `devops_brain.agents` – implements Planner, Executor, and Observer agents that map
  workflow actions to Python callables. Additional roles inherit from `BaseAgent`.
- `devops_brain.mcp` – stores adapter registry plus reference adapters for GitHub,
  Kubernetes, and CI.
- `devops_brain.workflows` – transforms YAML config into executable steps and aggregates
  runtime results into `WorkflowResult`.
- `automation/run_workflow.py` – automation-friendly wrapper for invoking workflows from
  CI, schedulers, or chatops integrations.

## Extending agents

1. Create a new class under `src/devops_brain/agents` that inherits from `BaseAgent`.
2. Implement action handlers following the `action_<name>` convention.
3. Add the role/class mapping inside `AGENT_TYPE_MAP` in `orchestrator.py`.
4. Register instances inside `configs/brain.yaml`.

## Extending adapters

1. Create a module under `src/devops_brain/mcp/adapters`.
2. Inherit from `MCPAdapter` and implement `action_<name>` helpers.
3. Register the adapter type inside `ADAPTER_TYPE_MAP`.
4. Add configuration under `mcp_adapters` within `configs/brain.yaml`.

## Designing workflows

Each workflow is a YAML file with:

- `name` / `description` metadata
- `triggers`: documentation for what kicks off the workflow
- `steps`: ordered entries with `agent`, `action`, optional `adapter`, and `inputs`

Example snippet:

```
steps:
  - name: Trigger CI pipeline
    agent: executor
    action: trigger-ci
    adapter: github
    inputs:
      workflow: release.yml
      inputs:
        release_type: hotfix
```

The orchestrator builds `AgentContext` objects for every step, passes them into the
specified agent, and persists returned outputs in shared memory for downstream steps.

## Automation integration

- **CLI** – use the Typer app (`devops-brain status|run|adapters`) for local control.
- **Automation runner** – `python automation/run_workflow.py <workflow>` is designed to
  plug into cron, CI, or chatops bots. The script prints JSON so upstream tools can parse
  success state and shared memory.
- **GitHub Actions** – wire the runner into a workflow file to kick off agent-driven
  orchestration on pushes or tags.
- **MCP servers** – as you implement adapters backed by MCP servers, update `brain.yaml`
  to point at the correct deployment/environment settings.

## Future enhancements

- Persist workflow state/history (SQLite, DynamoDB, etc.)
- Replace stub adapter actions with real API clients
- Add policy enforcement agents (SRE/Compliance)
- Enrich `AgentContext` with telemetry feeds and structured chat logs
