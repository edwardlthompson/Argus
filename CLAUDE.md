# Claude Code instructions

Canonical spec: `AGENTS.md`. Product brief: `AGENT.md`. Parent template: `edwardlthompson/agent-project-bootstrap` (see `docs/PARENT_GAP_LIST.md`).

## Do

- Follow BUILD_PLAN Sequential then Parallel
- Run `bash scripts/verify.sh` (or `scripts/verify.ps1`) before marking rows ✅
- Keep behaviour in `config/*.yaml`

## Do not

- Commit secrets or `.env`
- Push or deploy without `[HUMAN]` approval
- Force-push, rewrite history, or delete target repositories
