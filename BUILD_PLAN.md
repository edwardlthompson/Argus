# BUILD_PLAN — Argus

Status legend: 🔲 todo · ✅ done · ❌ blocked

## Product (do not drift)

<!-- product-brief-sync -->
Argus is the enforcer: multi-repo hygiene, scoring, gated apply, and (on the private runner only) hands-off YOLO. Public product ships YOLO off. MIT. Python 3.11+. Never invents rules. See `AGENT.md`.
<!-- /product-brief-sync -->

**Architecture (do not drift):** Public MIT product repo (source + CI). Private **runner** for scheduled scan/apply, Issues inbox, artifacts, secrets, YOLO. Public `USERNAME/USERNAME` profile Overview via PR. Never publish per-repo security findings on public product Pages/Issues.

> **Free-tier Actions-out** archived in COMPLETED_TASKS.md @ `e51fa8b`.
> When Actions minutes are gone: `argus local-weekly --apply` or `merge-upgrades --allow-unarmed --actions-unavailable` — **never** require a payment card.

## Non-goals (board)

- Overwriting sacred child files (`AGENTS.md`, `docs/spec.md`, `docs/plan.md`, product `branding/assets`)
- Force-push / deleting repos
- Vendoring full parent `modules/` / `examples/` / `scripts/lib` into Argus product (G12)
- Arming YOLO on public Argus
- Requiring a GitHub payment card / paid Actions minutes

## Sequential

| Status | Venue | Task |
|--------|-------|------|
| ✅ | `[AGENT][LOCAL]` — scope: reports/pages | **R1 Portfolio Pages + Steward** — sanitized public `portfolio-pages.html`; private `latest*` + `steward-brief.html` in argus-history; Pages never stages full report. |

## Parallel (after Sequential)

None.

## Archived Sprints

| Sprint | Complete | Archive |
|--------|----------|---------|
| Free-tier Actions-out (no payment) | 2026-11-11 | `COMPLETED_TASKS.md` |
| argus-weekly repair W1–W6 + S1–S2 | 2026-11-11 | `COMPLETED_TASKS.md` |
| Parent v1.13.0 child upgrades U1–U7 | 2026-11-11 | `COMPLETED_TASKS.md` |
| Signals → fleet → YOLO → remote S9–S15 | 2026-11-09 | `COMPLETED_TASKS.md` |
| Dual-plane + profile + Sequential A–L | 2026-11-05 | `COMPLETED_TASKS.md` |
| Sprints 0–8 + portfolio doctor + control plane + Cursor FOSS | 2026-11-05 | `COMPLETED_TASKS.md` |
