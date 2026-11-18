# UX apply (any IDE)

Ask your agent to implement **one** BUILD_PLAN UX inventory id to the construction law. In Cursor you can type `/ux-apply UX-NNN` instead.

## Paste prompt

```
Read docs/help/UX-APPLY.md and implement UX-NNN. Then scoped review. Do not drain the rest of the inventory.

```

## Recipe

1. Require an id. Set **Status:** `in_progress`.
2. Implement to [`docs/ux-ui-guidelines.md`](../ux-ui-guidelines.md) and `docs/DESIGN_GUIDE.md`. Smaller change that meets the law; leftover larger work is a new `UX-NNN`.
3. Tests (or feature-spec fallback). `python3 scripts/agent-run.py watch-agent-gates --once --autofix --scope auto`.
4. **Status:** `done` when Success is met. Scoped review of the same surface; append new findings.
5. Do not push unless `/push` or `/ship`.

See [`AGENT_PORTABILITY.md`](../AGENT_PORTABILITY.md) if your tool has no slash commands.
