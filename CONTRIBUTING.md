# Contributing

Thanks for helping with Argus.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
argus doctor
```

## Before you open a PR

1. Add or update tests for behaviour changes.
2. Run `bash scripts/verify.sh` (or `scripts/verify.ps1`).
3. Keep behaviour changes in `config/*.yaml` when possible.
4. Use Conventional Commits (`feat:`, `fix:`, `docs:`, …).

## Scope

Argus is a **controller**. Prefer PRs into target repos over direct commits. Never force-push or delete repositories.

## Parent template

This product child tracks [agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap). See `docs/PARENT_GAP_LIST.md` and `docs/UPGRADING_FROM_TEMPLATE.md`.
