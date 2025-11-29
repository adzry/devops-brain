#!/usr/bin/env python3
"""
DevOps Brain CLI

Command-line interface for interacting with DevOps Brain agents and services.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.syntax import Syntax
from rich import print as rprint

# Create Typer app
app = typer.Typer(
    name="devops-brain",
    help="🧠 DevOps Brain - AI-powered DevOps automation",
    add_completion=False,
)

# Rich console for pretty output
console = Console()

# Sub-commands
agents_app = typer.Typer(help="Manage and interact with agents")
tasks_app = typer.Typer(help="Manage tasks")
scan_app = typer.Typer(help="Run security and code scans")
test_app = typer.Typer(help="Testing operations")
infra_app = typer.Typer(help="Infrastructure operations")

app.add_typer(agents_app, name="agents")
app.add_typer(tasks_app, name="tasks")
app.add_typer(scan_app, name="scan")
app.add_typer(test_app, name="test")
app.add_typer(infra_app, name="infra")


# ============================================================================
# Helper Functions
# ============================================================================

def get_api_url() -> str:
    """Get the API URL from environment or default."""
    import os
    return os.environ.get("DEVOPS_BRAIN_API_URL", "http://localhost:8000")


async def api_request(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
) -> dict:
    """Make an API request."""
    import httpx
    
    url = f"{get_api_url()}{endpoint}"
    
    async with httpx.AsyncClient(timeout=300) as client:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()


def run_async(coro):
    """Run an async function."""
    return asyncio.run(coro)


def print_json(data: dict) -> None:
    """Print JSON data with syntax highlighting."""
    json_str = json.dumps(data, indent=2, default=str)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗ Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


# ============================================================================
# Main Commands
# ============================================================================

@app.command()
def version():
    """Show version information."""
    console.print(Panel.fit(
        "[bold cyan]DevOps Brain[/bold cyan]\n"
        "Version: 1.0.0\n"
        "Python: " + sys.version.split()[0],
        title="🧠 DevOps Brain",
    ))


@app.command()
def status():
    """Check the status of DevOps Brain services."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Checking services...", total=None)
        
        try:
            result = run_async(api_request("GET", "/health"))
            
            console.print()
            console.print(Panel.fit(
                f"[green]Status: {result['status']}[/green]\n"
                f"Version: {result['version']}",
                title="🧠 DevOps Brain Status",
            ))
            
            # Show agent status
            if "components" in result and "orchestrator" in result["components"]:
                orch = result["components"]["orchestrator"]
                if "agents" in orch:
                    table = Table(title="Registered Agents")
                    table.add_column("Agent", style="cyan")
                    table.add_column("Status", style="green")
                    
                    for agent, info in orch["agents"].items():
                        status = info.get("status", "unknown")
                        table.add_row(agent, status)
                    
                    console.print(table)
                    
        except Exception as e:
            print_error(f"Could not connect to API: {e}")
            raise typer.Exit(1)


@app.command()
def execute(
    action: str = typer.Argument(..., help="Action to execute"),
    payload: str = typer.Option("{}", "--payload", "-p", help="JSON payload"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Target agent"),
    priority: str = typer.Option("medium", "--priority", help="Task priority"),
    output: str = typer.Option("pretty", "--output", "-o", help="Output format: pretty, json"),
):
    """Execute an action on an agent."""
    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError:
        print_error("Invalid JSON payload")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(f"Executing {action}...", total=None)
        
        try:
            result = run_async(api_request("POST", "/api/v1/execute", {
                "action": action,
                "payload": payload_dict,
                "target_agent": agent,
                "priority": priority,
            }))
            
            console.print()
            
            if output == "json":
                print_json(result)
            else:
                status_color = "green" if result["status"] == "completed" else "red"
                console.print(Panel.fit(
                    f"[{status_color}]Status: {result['status']}[/{status_color}]\n"
                    f"Agent: {result['agent']}\n"
                    f"Duration: {result['duration_ms']}ms",
                    title=f"Task: {action}",
                ))
                
                if result.get("result"):
                    console.print("\n[bold]Result:[/bold]")
                    print_json(result["result"])
                
                if result.get("error"):
                    print_error(result["error"])
                    
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)


# ============================================================================
# Agent Commands
# ============================================================================

@agents_app.command("list")
def list_agents():
    """List all registered agents."""
    try:
        result = run_async(api_request("GET", "/api/v1/agents"))
        
        table = Table(title="Registered Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Capabilities", style="yellow")
        
        for agent in result["agents"]:
            caps = ", ".join(agent["capabilities"][:3])
            if len(agent["capabilities"]) > 3:
                caps += f" (+{len(agent['capabilities']) - 3} more)"
            table.add_row(agent["name"], agent["status"], caps)
        
        console.print(table)
        
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@agents_app.command("info")
def agent_info(agent_name: str = typer.Argument(..., help="Agent name")):
    """Get detailed information about an agent."""
    try:
        result = run_async(api_request("GET", f"/api/v1/agents/{agent_name}"))
        print_json(result)
        
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@agents_app.command("run")
def run_agent_action(
    agent_name: str = typer.Argument(..., help="Agent name"),
    action: str = typer.Argument(..., help="Action to execute"),
    payload: str = typer.Option("{}", "--payload", "-p", help="JSON payload"),
):
    """Run an action on a specific agent."""
    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError:
        print_error("Invalid JSON payload")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(f"Running {action} on {agent_name}...", total=None)
        
        try:
            result = run_async(api_request(
                "POST",
                f"/api/v1/agents/{agent_name}/execute",
                {"action": action, "payload": payload_dict},
            ))
            
            console.print()
            print_json(result)
            
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)


# ============================================================================
# Scan Commands
# ============================================================================

@scan_app.command("security")
def scan_security(
    target: str = typer.Option(".", "--target", "-t", help="Target directory"),
    scan_type: str = typer.Option("full", "--type", help="Scan type: full, quick"),
):
    """Run a security vulnerability scan."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Running security scan...", total=None)
        
        try:
            result = run_async(api_request("POST", "/api/v1/execute", {
                "action": "scan_vulnerabilities",
                "payload": {"target": target, "scan_type": scan_type},
                "target_agent": "security_agent",
            }))
            
            console.print()
            
            if result["status"] == "completed" and result.get("result"):
                data = result["result"]
                
                # Summary panel
                vulns = data.get("vulnerabilities_found", 0)
                color = "green" if vulns == 0 else "yellow" if vulns < 5 else "red"
                console.print(Panel.fit(
                    f"[{color}]Vulnerabilities Found: {vulns}[/{color}]",
                    title="🔒 Security Scan Results",
                ))
                
                # By severity
                if "by_severity" in data:
                    table = Table(title="By Severity")
                    table.add_column("Severity", style="bold")
                    table.add_column("Count")
                    
                    for sev, count in data["by_severity"].items():
                        color = {"critical": "red", "high": "yellow", "medium": "cyan"}.get(sev, "white")
                        table.add_row(f"[{color}]{sev.upper()}[/{color}]", str(count))
                    
                    console.print(table)
                
                # Recommendations
                if result.get("result", {}).get("recommendations"):
                    console.print("\n[bold]Recommendations:[/bold]")
                    for rec in result["result"]["recommendations"]:
                        console.print(f"  • {rec}")
            else:
                print_error(result.get("error", "Scan failed"))
                
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)


@scan_app.command("secrets")
def scan_secrets(
    target: str = typer.Option(".", "--target", "-t", help="Target directory"),
):
    """Scan for exposed secrets and credentials."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Scanning for secrets...", total=None)
        
        try:
            result = run_async(api_request("POST", "/api/v1/execute", {
                "action": "detect_secrets",
                "payload": {"target": target},
                "target_agent": "security_agent",
            }))
            
            console.print()
            print_json(result.get("result", result))
            
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)


# ============================================================================
# Test Commands
# ============================================================================

@test_app.command("generate")
def generate_tests(
    file: str = typer.Argument(..., help="File to generate tests for"),
    framework: str = typer.Option("pytest", "--framework", "-f", help="Test framework"),
):
    """Generate tests for a file."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Generating tests...", total=None)
        
        try:
            result = run_async(api_request("POST", "/api/v1/execute", {
                "action": "generate_tests",
                "payload": {"file": file, "framework": framework},
                "target_agent": "testing_agent",
            }))
            
            console.print()
            
            if result["status"] == "completed" and result.get("result"):
                data = result["result"]
                console.print(Panel.fit(
                    f"Generated {data.get('tests_generated', 0)} tests",
                    title="🧪 Test Generation",
                ))
                
                if "test_code" in data:
                    console.print("\n[bold]Generated Tests:[/bold]")
                    syntax = Syntax(data["test_code"], "python", theme="monokai")
                    console.print(syntax)
            else:
                print_error(result.get("error", "Generation failed"))
                
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)


@test_app.command("coverage")
def analyze_coverage(
    target: str = typer.Option("src/", "--target", "-t", help="Target directory"),
):
    """Analyze test coverage."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Analyzing coverage...", total=None)
        
        try:
            result = run_async(api_request("POST", "/api/v1/execute", {
                "action": "analyze_coverage",
                "payload": {"target": target},
                "target_agent": "testing_agent",
            }))
            
            console.print()
            print_json(result.get("result", result))
            
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)


# ============================================================================
# Infrastructure Commands
# ============================================================================

@infra_app.command("costs")
def analyze_costs(
    time_range: str = typer.Option("30d", "--range", "-r", help="Time range"),
):
    """Analyze infrastructure costs."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Analyzing costs...", total=None)
        
        try:
            result = run_async(api_request("POST", "/api/v1/execute", {
                "action": "analyze_costs",
                "payload": {"time_range": time_range},
                "target_agent": "infrastructure_agent",
            }))
            
            console.print()
            print_json(result.get("result", result))
            
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)


@infra_app.command("drift")
def detect_drift():
    """Detect infrastructure drift."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Detecting drift...", total=None)
        
        try:
            result = run_async(api_request("POST", "/api/v1/execute", {
                "action": "detect_drift",
                "payload": {},
                "target_agent": "infrastructure_agent",
            }))
            
            console.print()
            print_json(result.get("result", result))
            
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)


# ============================================================================
# Task Commands
# ============================================================================

@tasks_app.command("list")
def list_tasks(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum tasks to show"),
):
    """List recent tasks."""
    try:
        endpoint = f"/api/v1/tasks?limit={limit}"
        if status:
            endpoint += f"&status={status}"
        
        result = run_async(api_request("GET", endpoint))
        
        table = Table(title="Recent Tasks")
        table.add_column("Task ID", style="cyan")
        table.add_column("Agent", style="yellow")
        table.add_column("Action")
        table.add_column("Status", style="green")
        table.add_column("Duration")
        
        for task in result.get("tasks", []):
            status_color = {
                "completed": "green",
                "failed": "red",
                "running": "yellow",
            }.get(task["status"], "white")
            
            table.add_row(
                task["task_id"][:8] + "...",
                task["agent"],
                task["action"],
                f"[{status_color}]{task['status']}[/{status_color}]",
                f"{task['duration_ms']}ms",
            )
        
        console.print(table)
        
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@tasks_app.command("status")
def task_status(task_id: str = typer.Argument(..., help="Task ID")):
    """Get status of a specific task."""
    try:
        result = run_async(api_request("GET", f"/api/v1/tasks/{task_id}"))
        print_json(result)
        
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
