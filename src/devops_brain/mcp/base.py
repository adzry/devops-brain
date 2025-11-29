"""MCP adapter primitives for DevOps Brain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from devops_brain.config import MCPAdapterConfig
from devops_brain.utils.logging import get_logger


@dataclass(slots=True)
class MCPActionResult:
    """Outcome from calling an MCP adapter."""

    name: str
    success: bool
    message: str
    details: Dict[str, Any]


class MCPAdapter:
    """Base adapter that can execute actions against external systems."""

    def __init__(self, config: MCPAdapterConfig):
        self.config = config
        self.logger = get_logger(f"mcp.{config.name}")

    @property
    def name(self) -> str:
        return self.config.name

    def execute(self, action: str, payload: Dict[str, Any]) -> MCPActionResult:
        handler_name = f"action_{action.replace('-', '_')}"
        handler = getattr(self, handler_name, None)
        if handler:
            return handler(payload)

        self.logger.warning(
            "Adapter %s does not implement action '%s'. Falling back to noop.", self.name, action
        )
        return MCPActionResult(
            name=self.name,
            success=True,
            message=f"Noop action '{action}' executed.",
            details={"payload": payload},
        )


class MCPRegistry:
    """Stores adapter instances and routes execution."""

    def __init__(self):
        self._adapters: Dict[str, MCPAdapter] = {}

    def register(self, adapter: MCPAdapter) -> None:
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> MCPAdapter:
        if name not in self._adapters:
            raise KeyError(f"MCP adapter '{name}' has not been registered.")
        return self._adapters[name]

    def execute(self, adapter_name: str, action: str, payload: Dict[str, Any]) -> MCPActionResult:
        adapter = self.get(adapter_name)
        return adapter.execute(action, payload)

    def info(self) -> Dict[str, Any]:
        return {name: adapter.config.type for name, adapter in self._adapters.items()}
