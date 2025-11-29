# DevOps Brain

Production-ready scaffold for a multi-agent, config-driven DevOps automation brain,
designed to be orchestrated via Cursor and MCP (e.g. GitHub MCP server).

- Single sovereign Root agent with write authority.
- 7 core specialist agents + 10 additional advanced agents (17 total).
- Config-driven architecture via `configs/brain.yaml`.
- Workflows defined in YAML under `configs/workflows/`.
- Python orchestrator + CLI to execute workflows.

## Quick Start

1. Install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   pip install -e .
   ```

2. Configure MCP GitHub server in `.cursor/mcp.json` and set your PAT in Cursor.

3. From the project root, run the bootstrap workflow:

   ```bash
   ./scripts/bootstrap.sh
   ```

4. Or via Python entrypoint:

   ```bash
   python -m devops_brain.cli bootstrap
   ```

5. Extend or refine workflows under `configs/workflows/` and agent roles in `configs/brain.yaml`.
