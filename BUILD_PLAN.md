# BUILD_PLAN — Argus

Status legend: 🔲 todo · ✅ done · ❌ blocked

## Product (do not drift)

<!-- product-brief-sync -->
Argus is the enforcer: multi-repo hygiene, scoring, gated apply, and (on the private runner only) hands-off YOLO. Public product ships YOLO off. MIT. Python 3.11+. Never invents rules. See `AGENT.md`.
<!-- /product-brief-sync -->

**Architecture (do not drift):** Public MIT product repo (source + CI). Private **runner** for scheduled scan/apply, Issues inbox, artifacts, secrets, YOLO. Public `USERNAME/USERNAME` profile Overview via PR. Never publish per-repo security findings on public product Pages/Issues.

> **Parent upgrade wave v1.13.0** — U1–U7 PRs opened (canon rules). Merge after CI. Prior S9–S15 archived in COMPLETED_TASKS.md.

## Non-goals (board)

- Overwriting sacred child files (`AGENTS.md`, `docs/spec.md`, `docs/plan.md`, product `branding/assets`)
- Force-push / deleting repos
- Vendoring full parent `modules/` / `examples/` / `scripts/lib` into Argus product (G12)
- Arming YOLO on public Argus

## Sequential — Parent v1.13.0 child upgrades

| Status | Venue | Task |
|--------|-------|------|
| ✅ | `[AGENT][LOCAL]` — scope: `scripts/,BUILD_PLAN.md,dist/` | **U1 Tooling** — `scripts/child-upgrade-1.13.py` canon pack + inventory |
| ✅ | `[AGENT][LOCAL]` — scope: fleet | **U2 Canary** — `edwardlthompson/lineage-lens` full upgrade PR |
| ✅ | `[AGENT][LOCAL]` — scope: fleet | **U3 Batch** — AstroAlarm, HermesLauncher, SyncMark |
| ✅ | `[AGENT][LOCAL]` — scope: fleet | **U4 Batch** — chromaflow, OBDForge, JanusBoot, continuum-calendar, QuickMediaIngest |
| ✅ | `[AGENT][LOCAL]` — scope: fleet | **U5 Batch** — selfchronicle, ExpeditionGauge, takein-sms, hover-icons, 3d-game-optimizer |
| ✅ | `[AGENT][LOCAL]` — scope: fleet | **U6 Batch** — vault-organizer, noclip-auto, trendalgo-bot, MultiAppShare-, DevPulse |
| ✅ | `[AGENT][LOCAL]` — scope: fleet | **U7 Batch** — OpenShouter, point-and-shoot, QRaft, screen-wakelock-detector, starrupture-city-planner, aetherfeed, bl4-forge, Argus (product-safe pack) |

**Excluded:** `agent-project-bootstrap`, `edwardlthompson` (profile), `argus-runner`.

**Next (human/CI):** merge open `chore/argus-upgrade-1.13.0` PRs after checks green. `/upgrade` may still list Mixed/Sacred gaps (product README, AGENTS.md) — those stay human.

## Parallel (after Sequential)

None until upgrade PRs merge.

## Archived Sprints

| Sprint | Complete | Archive |
|--------|----------|---------|
| Signals → fleet → YOLO → remote S9–S15 | 2026-11-09 | `COMPLETED_TASKS.md` |
| Dual-plane + profile + Sequential A–L | 2026-11-05 | `COMPLETED_TASKS.md` |
| Sprints 0–8 + portfolio doctor + control plane + Cursor FOSS | 2026-11-05 | `COMPLETED_TASKS.md` |
