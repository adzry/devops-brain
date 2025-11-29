"""DevOps Brain package entrypoint."""

from importlib.metadata import version

__all__ = ["__version__"]


def _safe_version() -> str:
    try:
        return version("devops-brain")
    except Exception:
        return "0.0.0"


__version__ = _safe_version()
