"""Continuous integration MCP adapter."""

from __future__ import annotations

from typing import Any, Dict

from devops_brain.mcp.base import MCPActionResult, MCPAdapter


class CIAdapter(MCPAdapter):
    """Surface CI signals into the DevOps Brain."""

    def action_fetch_status(self, payload: Dict[str, Any]) -> MCPActionResult:
        pipeline = payload.get("pipeline") or self.config.settings.get("pipeline", "release")
        status = payload.get("status", "green")
        message = f"Pipeline {pipeline} status: {status}"
        self.logger.info(message)
        return MCPActionResult(
            name=self.name, success=True, message=message, details={"pipeline": pipeline, "status": status}
        )

    def action_attach_report(self, payload: Dict[str, Any]) -> MCPActionResult:
        report = payload.get("report", {})
        message = "Attached verification report."
        self.logger.info(message)
        return MCPActionResult(
            name=self.name,
            success=True,
            message=message,
            details={"report": report},
        )
