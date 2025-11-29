#!/usr/bin/env python3
"""Convenience entrypoint to execute workflows from automation engines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from devops_brain.orchestrator import DevOpsBrain


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DevOps Brain workflows")
    parser.add_argument("workflow", help="Workflow name")
    parser.add_argument(
        "--objective",
        "-o",
        default="Automated objective",
        help="Objective or mission for the workflow run",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path("configs/brain.yaml"),
        help="Path to brain configuration file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    brain = DevOpsBrain(str(args.config))
    result = brain.run_workflow(args.workflow, args.objective)
    print(json.dumps({"success": result.success, "state": result.shared_state}, indent=2))


if __name__ == "__main__":
    main()
