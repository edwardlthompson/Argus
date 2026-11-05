# Agent Router

1. **First read:** hook + `BUILD_PLAN.md` next row (full `docs/START_HERE.md` only on first day)
2. **Cursor modes:** Ask / Plan / Agent / Debug
3. **Task board:** `BUILD_PLAN.md` · Status: 🔲 · ✅ · ❌
4. **Living memory:** `.agent/AGENT_MEMORY.md` at milestones only. Read `AGENT.md` before sprint rows.
5. **Parent template:** [edwardlthompson/agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap) @ `.template-version` — see `docs/PARENT_GAP_LIST.md`

> Thin child of agent-project-bootstrap. Do not re-import the full template runtime unless a BUILD_PLAN row says so.

## Project Overview & Architecture

<!-- bootstrap-project-card -->
**Product:** Argus
**Purpose:** Multi-repo hygiene controller (discover → score → auto-safe apply → gated agents → grandma notify)
**Stack:** python
<!-- /bootstrap-project-card -->

- **Parent:** `edwardlthompson/agent-project-bootstrap` (product child, not template maintainer)
- **Package:** `argus/` · **Config-as-behaviour:** `config/*.yaml`
- **Outputs:** `dist/runbook.md`, `dist/report.html`
- **Spec:** `docs/spec.md` · **Plan:** `docs/plan.md` · **Brief:** `AGENT.md`

## Environment & Dependency Management

| Tool | Role |
|------|------|
| Python 3.11+ | Runtime + tests |
| Git | Required |
| `GITHUB_TOKEN` | Discovery / optional apply |

```bash
python -m venv .venv
pip install -e ".[dev]"
cp .env.example .env
```

## Build, Test, and Validation Commands

Before marking a BUILD_PLAN row ✅:

```bash
bash scripts/verify.sh
# Windows: powershell -File scripts/verify.ps1
```

Also useful: `argus doctor`, `pytest`, `ruff check argus tests`.

## Architecture Constraints

- FOSS MIT; no proprietary SDKs on the production path
- Max 300 lines static data (UI + i18n), 150 lines pure logic
- Deterministic scoring/composition — no LLMs on that path
- Prefer PRs; never force-push or delete target repos
- Every agent/auto_safe fix requires an executable `gate`

## Session Protocol

1. Next 🔲 `[AGENT][LOCAL]` from BUILD_PLAN (or empty board).
2. Skim CHANGELOG `[Unreleased]` (~20 lines).
3. After AGENT steps: `scripts/verify.sh`.
4. Milestone → `.agent/AGENT_MEMORY.md` / `.agent/DECISION_LOG.md`.
5. 3-strike → halt.

Replies: brief (1–3 sentences) unless Plan/Debug needs more.

## Multi-Agent Adapters

Source of truth: this file. Thin generated-style adapters:

| Target | File |
|--------|------|
| Cursor | `.cursor/rules/main.mdc` |
| Claude Code | `CLAUDE.md` |
| Cline | `.clinerules` |
| Gemini | `GEMINI.md` (pointer only) |
