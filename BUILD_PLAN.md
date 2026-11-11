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

**YOLO hands-off:** fix+soft-merge on scheduled run; `argus-weekly` = Tuesday 14:00 UTC on **private `argus-runner` only** (public product = dispatch-only, no cron); Grok **Tuesday Steward** digests leftovers (never merges). Sync weekly job body + cron to `argus-runner`. Leftovers = Security/Trivy/CodeQL/Feature Gate — human.

## Sequential — argus-weekly repair (found by Tuesday Steward 2026-11-10)

| Status | Venue | Task |
|--------|-------|------|
| 🔲 | `[HUMAN][PC]` — scope: Actions secrets | **W1 Token** — Add fine-grained `ARGUS_GITHUB_TOKEN` on **`edwardlthompson/argus-runner`** (not public Argus). Empty token → `GET /user` 403. Failed public run: https://github.com/edwardlthompson/Argus/actions/runs/42897596779 |
| 🔲 | `[HUMAN][PC]` — scope: workflow | **W2 Re-run** — re-run `argus-weekly` on the runner; confirm `argus-dist` (health-delta.md, health-hotspots.json, health-infographic) + Steward webhook. |
| 🔲 | `[HUMAN][PC]` — scope: runner | **W3 Where it runs** — Confirm Tuesday cron only on `argus-runner` after public cron removal; sync runner `weekly.yml` if still Monday. |
| ✅ | `[AGENT][LOCAL]` — scope: PRs | **W4 Dependabot** — Merged Actions bumps (#1,#2,#3,#4) + setup-python@v7 locally (closes #7 intent); **hold** pytest/pytest-cov majors (#6,#9). |

## Parallel (after Sequential)

None until upgrade PRs merge.

## Archived Sprints

| Sprint | Complete | Archive |
|--------|----------|---------|
| Signals → fleet → YOLO → remote S9–S15 | 2026-11-09 | `COMPLETED_TASKS.md` |
| Dual-plane + profile + Sequential A–L | 2026-11-05 | `COMPLETED_TASKS.md` |
| Sprints 0–8 + portfolio doctor + control plane + Cursor FOSS | 2026-11-05 | `COMPLETED_TASKS.md` |
