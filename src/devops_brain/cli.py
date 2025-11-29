"""Typer CLI for DevOps Brain."""

from __future__ import annotations

from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from devops_brain.orchestrator import DevOpsBrain

console = Console()
app = typer.Typer(help="Control the DevOps Brain automation system.")


def _build_brain(config: Path | None) -> DevOpsBrain:
    return DevOpsBrain(str(config) if config else None)


@app.command()
def status(config: Path = typer.Option(Path("configs/brain.yaml"), help="Config path")) -> None:
    """Print the currently registered resources."""

    brain = _build_brain(config)
    console.print(f"[bold green]Config:[/bold green] {brain.config_path}")

    table = Table(title="Agents", header_style="bold magenta", box=box.SIMPLE_HEAVY)
    table.add_column("Name")
    table.add_column("Role")
    for name, role in brain.list_agents().items():
        table.add_row(name, role)
    console.print(table)

    table = Table(title="Workflows", header_style="bold cyan", box=box.SIMPLE_HEAVY)
    table.add_column("Name")
    table.add_column("Description")
    for name, desc in brain.list_workflows().items():
        table.add_row(name, desc)
    console.print(table)


@app.command()
def run(
    workflow: str = typer.Argument(..., help="Workflow name, e.g. release"),
    objective: str = typer.Option("Ship stable release", "--objective", "-o"),
    config: Path = typer.Option(Path("configs/brain.yaml"), "--config", "-c"),
) -> None:
    """Execute a workflow end-to-end."""

    brain = _build_brain(config)
    result = brain.run_workflow(workflow, objective)
    status_text = "[green]SUCCESS[/green]" if result.success else "[red]FAILED[/red]"
    console.print(f"[bold]Workflow[/bold] {workflow}: {status_text}")
    for step_result in result.steps:
        console.print(f"- {step_result.summary}")
    console.print("Shared state:", result.shared_state)


@app.command()
def adapters(config: Path = typer.Option(Path("configs/brain.yaml"), "--config", "-c")) -> None:
    """Enumerate registered adapters."""

    brain = _build_brain(config)
    table = Table(title="MCP Adapters", header_style="bold yellow", box=box.SIMPLE_HEAVY)
    table.add_column("Name")
    table.add_column("Type")
    for name, adapter_type in brain.list_adapters().items():
        table.add_row(name, adapter_type)
    console.print(table)


if __name__ == "__main__":
    app()
