> **Argus product child:** template steps that need full agent-run/modules are N/A (G12/G14). Prefer `docs/START_HERE.md`, `docs/PUBLISH.md`, and `python scripts/agent-run.py verify`.
# Stack prune verification

Init stack selection is in `.cursor/stack-selection.json`.
Read @AGENT_MEMORY.md active modules (checkboxes synced by init-project).
Confirm pruned `examples/` and `modules/` match the chosen stack; never delete LICENSE, CI, or scripts/.
Run `python3 scripts/agent-run.py validate-template-index` if modules changed.

Begin now.
