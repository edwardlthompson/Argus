# BUILD_PLAN — Argus

<!-- remaining-tally -->
**Remaining:** AGENT 0 · LOCAL 0 · CLOUD 0 · AUTO 1 · HUMAN 1 · **2 open**
<!-- /remaining-tally -->

Status legend: 🔲 todo · ✅ done · ❌ blocked

## Product (do not drift)

<!-- product-brief-sync -->
Argus is the enforcer: multi-repo hygiene, scoring, gated apply, and (on the private runner only) hands-off YOLO. Public product ships YOLO off. MIT. Python 3.11+. Never invents rules. See `AGENT.md`.
<!-- /product-brief-sync -->

**Architecture (do not drift):** Public MIT product repo (source + CI). Private **runner** for scheduled scan/apply, Issues inbox, artifacts, secrets, YOLO. Public `USERNAME/USERNAME` profile Overview via PR. Never publish per-repo security findings on public product Pages/Issues.

> Goal: **continuous zero** — every `--apply` / `local-weekly --apply` / armed YOLO run clears mechanical open fixes automatically. BUILD_PLAN tracks product work for that loop, not a weekly punch list of findings.

## Non-goals (board)

- Overwriting sacred child files (`AGENTS.md`, `docs/spec.md`, `docs/plan.md`, product `branding/assets`)
- Force-push / deleting repos
- Vendoring full parent `modules/` / `examples/` / `scripts/lib` into Argus product (G12)
- Arming YOLO on public Argus
- Requiring a GitHub payment card / paid Actions minutes
- Inventing patches for red CI without a gate
- Filing portfolio **findings** as BUILD_PLAN chores (product auto-clears them). Marker-lane / APB-format hygiene on target boards is a gated fix (`BOARD-MARKERS` / `BOARD-RESTRUCTURE`), not a finding punch list.

## Sequential — Continuous zero product

| Status | Venue | Task |
|--------|-------|------|
| ✅ | `[AGENT][LOCAL]` — scope: reports/pages | **R1 Portfolio Pages + Steward** — sanitized public Pages; private `latest*` + steward brief. |
| ✅ | `[AGENT][LOCAL]` — scope: `config/safety.yaml,config_loader` | **CZ1 Safety continuous-zero flags** — `normal.yolo_handlers` / `auto_rules_sync` / `continuous_zero` / `second_pass`; YOLO `apply_api_handlers` / `resolve_ci_when_actions_unavailable`. |
| ✅ | `[AGENT][LOCAL]` — scope: `argus/signals/contract.py` | **CZ2 Signal fan-out fix** — `RULES-STALE` controller-only; `SEC-RELEASE-TOKEN-MISSING` opt-in `ARGUS_REQUIRE_RELEASE_TOKEN`. |
| ✅ | `[AGENT][LOCAL]` — scope: `argus/yolo.py,pipeline.py` | **CZ3 Handlers + pipeline loop** — vanilla handlers, API-safe human ids, CI soft-resolve, auto rules sync, second pass. |
| ✅ | `[AGENT][LOCAL]` — scope: `config/fixes/` | **CZ4 Fix catalogue** — CodeQL + lineage → agent; Dependabot/rules/token aligns with continuous zero. |
| ✅ | `[AGENT][LOCAL]` — scope: docs | **CZ5 Docs** — YOLO/SAFETY continuous-zero; this board. |
| ✅ | `[AGENT][LOCAL]` — scope: `argus/board_*.py,config/fixes/portfolio.yaml` | **B1 BUILD_PLAN normalize** — `BOARD-MARKERS` auto_safe + `BOARD-RESTRUCTURE` gated agent; fold News inbox. |
| ✅ | `[AGENT][LOCAL]` — scope: `argus/dependabot_policy.py,config/safety.yaml` | **D1 Dependabot merge policy** — mode-aware levels; CI-green via `evaluate_pre_merge`; no Actions-unavailable skip. |
| ✅ | `[AGENT][LOCAL]` — scope: `argus/release_*.py,config/releases.yaml` | **RF1 Release freshness** — local `argus releases` CLI (REST); tag-only prep PRs; not on Actions. |

## Parallel (operator cadence — not chores)

| Status | Venue | Task |
|--------|-------|------|
| 🔲 | `[AUTO][LOCAL]` — scope: weekly | **A1 Cadence** — Tuesday `local-weekly --apply` or armed runner YOLO. No BUILD_PLAN edits for open-fix counts. |
| 🔲 | `[HUMAN][PC]` — scope: judgment | **H1 Judgment only** — brand art, park/archive, residual Dependabot accept/dismiss after automation. |

### Open PRs (synced)

> Auto-managed on product repos. Do not hand-edit rows inside the markers.

<!-- open-prs-sync:begin -->
_No open Dependabot or Release Please PRs._
<!-- open-prs-sync:end -->

### Template gaps (synced)

> Auto-managed Monday cron + `sync-template-gaps-build-plan`. Do not hand-edit inside markers.

<!-- template-gaps-sync:begin -->
_No template gaps; Argus is a product child (see `docs/PARENT_GAP_LIST.md`)._
<!-- template-gaps-sync:end -->

### Local agent (This Computer)

Standing queue for This Computer. Rows: `🔲 [AGENT][LOCAL] … — scope: path`. `/build` claims these only.

<!-- local-agent-lane:begin -->
- 🔲 [AGENT][LOCAL] Flag repos at risk of Dependabot alert pause — scope: argus/signals/ (news P1, 2026-11-13) https://github.blog/changelog/2026-11-10-dependabot-alerts-will-pause-on-inactive-repositories
- 🔲 [AGENT][LOCAL] Add a check for unpinned MCP/agent npm packages — scope: config/fixes/ (news P2, 2026-11-13) https://github.com/advisories/GHSA-72xc-q3v8-7grp
- 🔲 [AGENT][LOCAL] Audit the repo for wfx-loot IOCs — scope: .github/ (news P1, 2026-11-14) https://blog.gitguardian.com/wfx-loot-a-ci-secret-stealer-pushed-with-stolen-github-credentials/
- 🔲 [AGENT][LOCAL] Add a fleet rule flagging wfx-loot IOCs and new npm lifecycle hooks — scope: config/fixes/ (news P2, 2026-11-14) https://blog.gitguardian.com/wfx-loot-a-ci-secret-stealer-pushed-with-stolen-github-credentials/
- 🔲 [AGENT][LOCAL] Propagate a "never paste secrets into agent chats" AGENTS.md rule to child repos — scope: argus/rules_sync.py (news P2, 2026-11-15) https://cursor.com/blog/security-incident-update
- 🔲 [AGENT][LOCAL] Add a hygiene rule that flags `on: pull_request_target` in public repo workflows — scope: config/fixes/ (news P2, 2026-11-16) https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/
<!-- local-agent-lane:end -->

### Cloud agent (Cursor Cloud)

Standing queue for Cursor Cloud. Rows: `🔲 [AGENT][CLOUD] … — scope: path`. Cloud claims these only.

<!-- cloud-agent-lane:begin -->
_No cloud agent items._
<!-- cloud-agent-lane:end -->

## Archived Sprints

| Sprint | Complete | Archive |
|--------|----------|---------|
| Overview sync + Fleet report (v0.9.0) | 2026-11-12 | `COMPLETED_TASKS.md` |
| Continuous zero + Issue triage (v0.8.0) | 2026-11-12 | `COMPLETED_TASKS.md` |
| Free-tier Actions-out (no payment) | 2026-11-11 | `COMPLETED_TASKS.md` |
| argus-weekly repair W1–W6 + S1–S2 | 2026-11-11 | `COMPLETED_TASKS.md` |
| Parent v1.13.0 child upgrades U1–U7 | 2026-11-11 | `COMPLETED_TASKS.md` |
| Signals → fleet → YOLO → remote S9–S15 | 2026-11-09 | `COMPLETED_TASKS.md` |
| Dual-plane + profile + Sequential A–L | 2026-11-05 | `COMPLETED_TASKS.md` |
| Sprints 0–8 + portfolio doctor + control plane + Cursor FOSS | 2026-11-05 | `COMPLETED_TASKS.md` |

## News inbox (synced)

P1/P2 tasks auto-synced by News Bot from [`docs/NEWS_INBOX.md`](docs/NEWS_INBOX.md).

- 🔲 [HUMAN][PC] Update Git to 2.56.1+ on dev PCs and WSL, and have Argus flag hosts below the patched version (news P2, 2026-11-16) https://github.blog/open-source/git/git-security-vulnerabilities-announced-7/
