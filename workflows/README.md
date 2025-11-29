# Automation Workflows

This directory contains automation workflow definitions for the DevOps Brain system.

## Structure

- `pr_workflow.yaml` - Pull request automation workflow
- `ci_workflow.yaml` - Continuous integration workflow
- `deploy_workflow.yaml` - Deployment automation workflow

## Workflow Engine

Workflows are executed by the DevOps Brain orchestrator and can trigger cloud agents,
run scripts, and integrate with external services via MCP adapters.
