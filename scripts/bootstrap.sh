#!/usr/bin/env bash
set -e

# Simple bootstrap runner for DevOps Brain
# Usage: ./scripts/bootstrap.sh

if [ -z "$VIRTUAL_ENV" ]; then
  echo "[devops-brain] Warning: no virtualenv active. Consider creating one."
fi

python -m devops_brain.cli bootstrap
