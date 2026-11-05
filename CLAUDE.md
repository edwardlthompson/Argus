# Claude Code instructions

Canonical spec: `AGENTS.md`. Product brief: `AGENT.md`. Parent template: `edwardlthompson/agent-project-bootstrap` (see `docs/PARENT_GAP_LIST.md`).

## Do

- Follow BUILD_PLAN Sequential then Parallel
- Run `python scripts/agent-run.py verify` (or `scripts/verify.*`) before marking rows ✅
- Keep behaviour in `config/*.yaml`
- Slash commands: `.cursor/commands/` · help: `docs/help/BATCH_COMMANDS.md`

## Do not

- Commit secrets or `.env`
- Push or deploy without `[HUMAN]` approval
- Force-push, rewrite history, or delete target repositories
