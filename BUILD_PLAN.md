# BUILD_PLAN — Argus

Status legend: 🔲 todo · ✅ done · ❌ blocked

## Product (do not drift)

<!-- product-brief-sync -->
Argus is a controller repository for multi-repo hygiene, scoring, safe auto-apply, gated agentic execution, and grandma-simple notifications. MIT. Python 3.11+. Portfolio doctor for the operator’s GitHub collection (including Argus itself). See `AGENT.md`.
<!-- /product-brief-sync -->

**Architecture (do not drift):** Public MIT product repo (source + CI). Private **runner** fork/repo for scheduled scan/`--apply`, Issues inbox, artifacts, secrets. Public `USERNAME/USERNAME` profile Overview README updated via PR from live data. Not agent-only; no local desktop app required for the core loop. Never publish per-repo security findings on public product Pages/Issues.

> **Sprints 0–8 + portfolio doctor + private control plane + Cursor FOSS** archived in COMPLETED_TASKS.md @ `39c34ef`.
> **Dual-plane + profile + Sequential A–L** archived in COMPLETED_TASKS.md (v0.3.0).

## Non-goals (board)

- Agent-only runtime · local desktop app · LLM-invented profile bios · findings on public product Issues/Pages

## Sequential

| Status | Venue | Task |
|--------|-------|------|
| — | — | *(empty — next ideas via `/ideas` or `/allideas`)* |

## Parallel (after Sequential)

None until a new Sequential lock.

## Archived Sprints

| Sprint | Complete | Archive |
|--------|----------|---------|
| Dual-plane + profile + Sequential A–L | 2026-11-05 | `COMPLETED_TASKS.md` |
| Sprints 0–8 + portfolio doctor + control plane + Cursor FOSS | 2026-11-05 | `COMPLETED_TASKS.md` |
