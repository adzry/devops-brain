"""Reference MCP adapters."""

from .ci import CIAdapter
from .github import GitHubAdapter
from .kubernetes import KubernetesAdapter

__all__ = ["GitHubAdapter", "KubernetesAdapter", "CIAdapter"]
