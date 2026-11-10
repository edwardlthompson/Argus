# BUILD_PLAN — Argus

Status legend: 🔲 todo · ✅ done · ❌ blocked

## Product (do not drift)

<!-- product-brief-sync -->
Argus is the enforcer: multi-repo hygiene, scoring, gated apply, and (on the private runner only) hands-off YOLO. Public product ships YOLO off. MIT. Python 3.11+. Never invents rules. See `AGENT.md`.
<!-- /product-brief-sync -->

**Architecture (do not drift):** Public MIT product repo (source + CI). Private **runner** for scheduled scan/apply, Issues inbox, artifacts, secrets, YOLO. Public `USERNAME/USERNAME` profile Overview via PR. Never publish per-repo security findings on public product Pages/Issues.

> **S9–S15 signals → fleet → YOLO → remote** archived in COMPLETED_TASKS.md (2026-11-09).
> **Sprints 0–8 + portfolio doctor + private control plane + Cursor FOSS** archived in COMPLETED_TASKS.md @ `39c34ef`.
> **Dual-plane + profile + Sequential A–L** archived in COMPLETED_TASKS.md (v0.3.0).
> **v0.4.0 YOLO + reports** shipped 2026-11-05.

## Non-goals (board)

- Agent-only runtime · local desktop app · LLM-invented profile bios · findings on public product Issues/Pages · YOLO armed on the public product template

## Sequential

| Status | Venue | Task |
|--------|-------|------|
| — | — | *(empty — next work opens a new Sequential block)* |

## Parallel (after Sequential)

None until a new Sequential lock is opened.

## Archived Sprints

| Sprint | Complete | Archive |
|--------|----------|---------|
| Signals → fleet → YOLO → remote S9–S15 | 2026-11-09 | `COMPLETED_TASKS.md` |
| Dual-plane + profile + Sequential A–L | 2026-11-05 | `COMPLETED_TASKS.md` |
| Sprints 0–8 + portfolio doctor + control plane + Cursor FOSS | 2026-11-05 | `COMPLETED_TASKS.md` |
