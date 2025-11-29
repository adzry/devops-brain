"""
MCP Adapters Package

Provides adapter implementations for integrating DevOps Brain
with external services via the Model Context Protocol.
"""

from .base_adapter import BaseAdapter
from .github_adapter import GitHubAdapter
from .slack_adapter import SlackAdapter
from .database_adapter import DatabaseAdapter
from .monitoring_adapter import MonitoringAdapter

__all__ = [
    "BaseAdapter",
    "GitHubAdapter",
    "SlackAdapter", 
    "DatabaseAdapter",
    "MonitoringAdapter",
]

__version__ = "1.0.0"
