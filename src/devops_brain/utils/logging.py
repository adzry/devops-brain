"""Lightweight logging helpers."""

from __future__ import annotations

import logging
from typing import Optional

LOG_FORMAT = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name or "devops-brain")
