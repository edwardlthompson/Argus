# BUILD_PLAN — Argus

<!-- remaining-tally -->
**Remaining:** AGENT 2 · LOCAL 2 · CLOUD 0 · AUTO 1 · HUMAN 10 · **13 open**
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
- Filing portfolio **findings** as BUILD_PLAN chores (product auto-clears them). Marker-lane / APB-format hygiene on target boards is a gated fix (`BOARD-MARKERS` / `BOARD-RESTRUCTURE` / `BOARD-QUEUE-VISIBILITY`), not a finding punch list.

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

## Sequential — argus-runner weekly diagnostics (found by Tuesday Steward 2026-11-27)

Private `edwardlthompson/argus-runner` workflow `argus-weekly` failed all 4 runs (2026-11-09, 11-11, 11-17, 11-24). Job `run` lasted ~1s each time, uploaded 0 artifacts, and job logs returned 404 via the API. Latest: https://github.com/edwardlthompson/argus-runner/actions/runs/45509728786. No `health-delta.md`, `health-hotspots.json`, or health-infographic since 2026-11-12 (`argus-history/reports/latest.md` is stale). Runner `argus-report` has never run; runner `argus-scan` last failed 2026-11-10. Public Argus `argus-weekly` run #2 (https://github.com/edwardlthompson/Argus/actions/runs/42897596779) failed 403 on `GET /user` because `ARGUS_GITHUB_TOKEN` was empty. Repair PR #14 (W1–W4) was closed unmerged. W4 Dependabot majors were finished later and stay closed. Still open from that repair: the runner token must be non-empty (W1), a re-run must actually upload artifacts and ping Steward (W2), and hosted jobs still never start (archived W5).

| Status | Venue | Task |
|--------|-------|------|
| 🔲 | `[HUMAN][PC]` — scope: Actions UI | **D1 Read the 1s failure** — Open https://github.com/edwardlthompson/argus-runner/actions/runs/45509728786 and the 2026-11-09, 11-11, and 11-17 runs. Job `run` ~1s, 0 artifacts, API logs 404. Read the first failing step and any **Set up job** annotations. Startup causes to match: invalid workflow YAML; missing or unauthorized `uses:` (`actions/checkout@v7`, `actions/setup-python@v7`, `actions/upload-artifact@v7`; no reusable workflow); `runs-on` label unavailable; Actions disabled or minutes/spending limit exhausted; private-repo permission. |
| 🔲 | `[HUMAN][PC]` — scope: Actions billing | **D2 Actions enabled + minutes** — On `edwardlthompson/argus-runner`, confirm Actions is enabled and the account is inside its minutes and spending limit. If the block is billing, do not add a payment card (board non-goal). Record it and keep the Tuesday pass on `scripts/local-weekly.ps1` / `.sh` until hosted jobs start. |
| 🔲 | `[AGENT][LOCAL]` — scope: `argus-runner:.github/workflows/weekly.yml` | **D3 actionlint on default branch** — `actionlint` runner `weekly.yml` on default branch `main`. Expect name `argus-weekly`, cron `0 14 * * 2` plus `workflow_dispatch`, concurrency group `weekly-${{ github.workflow }}` with `cancel-in-progress: false`, job `run`, `runs-on: ubuntu-latest`. |
| 🔲 | `[HUMAN][PC]` — scope: runner label | **D4 runs-on** — Job `run` asks for GitHub-hosted `ubuntu-latest`. Confirm that label is allowed on this private repo. This workflow does not use a self-hosted runner label. |
| 🔲 | `[HUMAN][PC]` — scope: Actions secrets | **D5 ARGUS_GITHUB_TOKEN** — On **argus-runner** (the public repo secret was empty), confirm `ARGUS_GITHUB_TOKEN`: PAT with `repo` and `workflow` scope for every allowlisted repo. Weekly step **Run** also reads `GITHUB_TOKEN`, `ARGUS_DISCORD_WEBHOOK`, `ARGUS_TELEGRAM_BOT_TOKEN`, `ARGUS_TELEGRAM_CHAT_ID`, `ARGUS_WEBHOOK_URL`, and var `ARGUS_REPORT_URL`. Step **Ping Tuesday Steward** reads `GROK_STEWARD_WEBHOOK_URL` and `GROK_STEWARD_WEBHOOK_KEY`. Carry-forward of PR #14 W1. |
| 🔲 | `[HUMAN][PC]` — scope: token expiry | **D6 Token expiry** — Check `ARGUS_GITHUB_TOKEN` expiration and that Contents plus workflow scopes still cover the allowlist. A ~1s job dies before step **Run**, so expiry is the check once startup succeeds. |
| 🔲 | `[HUMAN][PC]` — scope: workflow_dispatch | **D7 Dispatch weekly** — `workflow_dispatch` `argus-weekly` on the runner (leave `apply` empty). Confirm **Upload private artifacts** publishes `argus-dist` containing `dist/health-delta.md`, `dist/health-hotspots.json`, `dist/health-infographic.svg`, and `dist/health-infographic.html`, and **Ping Tuesday Steward (optional Grok webhook)** posts when `GROK_STEWARD_WEBHOOK_URL` is set. Carry-forward of PR #14 W2. |
| 🔲 | `[HUMAN][PC]` — scope: argus-report | **D8 Run argus-report once** — Never run. Dispatch job `report` with required `target` (for example `edwardlthompson`) and `public_only=true`. Confirm **Upload artifacts** (`name: argus-report`, `path: dist/`). Step **Report** receives only `secrets.GITHUB_TOKEN`. Weekly and scan also pass `ARGUS_GITHUB_TOKEN` and prefer it when set; a 403 on other repos means the report workflow needs that same swap. |
| 🔲 | `[HUMAN][PC]` — scope: argus-scan | **D9 Open the scan failure** — `argus-scan` last failed 2026-11-10. Open that run (job `scan`, `runs-on: ubuntu-latest`, artifact `argus-scan-dist`). The same ~1s / 0-artifact startup closes with D1–D2. Otherwise record the first failing step (`Install` or `Scan`). After the cause is fixed, dispatch `apply=false` and confirm `argus-scan-dist`. |
| 🔲 | `[AGENT][LOCAL]` — scope: `.github/workflows/scan.yml` | **D10 Fix argus-scan** — When D9 is a workflow or **Scan** step defect (billing stays D2), patch runner `scan.yml` and the public Argus copy: job `scan`, `ARGUS_GITHUB_TOKEN` overriding `GITHUB_TOKEN`, upload `argus-scan-dist`. |
| 🔲 | `[HUMAN][PC]` — scope: public weekly | **D11 Public weekly** — Decide whether to disable public Argus `argus-weekly`. It is already `workflow_dispatch` only; cron `0 14 * * 2` stays on the runner. Run #2 returned 403 because public `ARGUS_GITHUB_TOKEN` was empty (PR #14 W3). Leave dispatch, or disable the workflow in the UI. Leave `schedule` off the public workflow. |

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
- 🔲 [AGENT][LOCAL] Add a fleet check for agent-framework 1.26.1/1.26.2 and unexpected .pth startup hooks — scope: config/fixes/ (news P2, 2026-11-18) https://www.wiz.io/blog/malicious-version-of-microsofts-agent-framework-published-to-pypi
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

### Waiting on a person

- 🔲 [HUMAN][PC] Update Git to 2.56.1+ on dev PCs and WSL, and have Argus flag hosts below the patched version (news P2, 2026-11-16) https://github.blog/open-source/git/git-security-vulnerabilities-announced-7/
