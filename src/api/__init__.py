"""
DevOps Brain API

FastAPI-based REST API for the DevOps Brain platform.
"""

from .main import app, create_app

__all__ = ["app", "create_app"]
