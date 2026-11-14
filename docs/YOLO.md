# YOLO mode (hands-off — private runner only)

YOLO is Argus’s **private-runner apply policy**: gated `auto_safe` + mechanical handlers + squash-merge of Argus PRs and **all Dependabot bump levels** (after CI is actually green) in one loop. It is **not** “Grok can push anything.”

## Dual-plane (locked)

| Plane | YOLO |
|-------|------|
| **Public product / template** (`edwardlthompson/Argus`) | **Off** — `apply_mode: normal`, no `yolo.on` (vanilla `--apply` still fix/heals upgrades and auto-merges Dependabot **patch+minor** after CI green; upgrade merges stay human — see [SAFETY.md](SAFETY.md)) |
| **Private operator runner** (`YOU/argus-runner`) | **On** — bootstrap writes `yolo.on` + runner `apply_mode: yolo` |

See [`docs/GROK_BOTS.md`](GROK_BOTS.md) and [ADR 0001](adr/0001-grok-bots-draft-digest-and-yolo.md).

## Arming

Preferred arm file on the **runner**: `yolo.on` (created by `scripts/bootstrap-argus-runner.*`).

Sticky kill switches:

- Delete `yolo.on` and/or write `YOLO-OFF.md`
- Or set runner `apply_mode: normal`

Public product must stay `apply_mode: normal` so forks/scanners are dry-run safe by default.

## Config (runner)

```yaml
apply_mode: yolo   # normal | yolo — product ships normal

yolo:
  skip_profile: true   # do not auto_safe / merge into YOU/YOU
  sync_profile: true   # still refresh Overview PR (stars/forks/views/icons/membership)
  auto_merge_auto_safe: true
  auto_merge_dependabot: true
  dependabot_auto_merge_levels: [patch, minor, major]
  auto_dispatch_agents: true
  auto_merge_agent_prs: true
  max_auto_merges_per_day: 80
  max_yolo_actions_per_run: 100
  close_stale_bot_prs_days: 14
  stale_pr_idle_days: 30
  second_pass_if_budget: true
```

### YOLO implies apply

When YOLO is armed, `argus run` / `argus fix` **apply** unless you pass `--dry-run`. **`sync_profile: true`** (default) refreshes the public `YOU/YOU` Overview on every apply / Tuesday weekly / `local-weekly` — live stars, forks, watches, Insights views, icon rescan, and public↔private membership. `skip_profile` only blocks auto_safe/merge *into* the Overview repo. Pass `--skip-profile` to disable Overview sync for one run.

## Six pre-merge checks

Before squash-merge (Argus chore PRs, parent upgrades, **and Dependabot**): armed · hard floors · prefer PRs · title policy · CI green · not sacred profile.

Dependabot never uses `skip_ci_when_actions_unavailable`, billing skip, or soft-allowlist. Empty/never-started checks are **not** green — the PR stays open. Vanilla `--apply` uses the same evaluation with `require_armed=false` and `normal.dependabot_auto_merge_levels` (patch+minor).

## Parent upgrade merges

When `yolo.auto_merge_upgrade_prs: true` (default), YOLO also squash-merges open PRs titled `upgrade parent rules` on heads `chore/argus-upgrade-*` after CI is green (or no checks). Operator one-shot from a product clone:

```bash
argus fix-upgrades --allow-unarmed
argus merge-upgrades --allow-unarmed --fix --soft-allowlist --loop 10 --sleep 180
```

`--fix` / scheduled YOLO runs a **mandatory clear loop** (`clear_upgrade_blockers`): heal + mechanical fixers (markdown pipes, F-Droid stubs, ADR Status→Accepted, CodeQL android drop when pruned, conventional titles, **Trivy npm overrides + lockfile regen**) → wait for CI → soft-merge → repeat. Soft-merge is template/hygiene noise only (`Template Upgrade Simulation`, `Validate Bootstrap Artifacts`, Conventional Commits title, …; umbrella `CI` ignored). **Hard floors stay:** Security/Trivy/CodeQL/Gitleaks/Dependency Review/Scorecard and product Feature Gate/build/ADR/assemble failures never soft-merge — fixers must clear them or they stay on the digest. Expand `NPM_OVERRIDES` / `CAPACITOR_PINS` in `argus/yolo_trivy_npm.py` when new recurring CVEs appear.

**Hands-off defaults** (`config/safety.yaml` → `yolo`): `clear_upgrade_blockers: true`, `clear_upgrade_loops: 8`, `fix_upgrade_prs: true`, `soft_merge_upgrade_noise: true`, `auto_merge_upgrade_prs: true`, `merge_when_actions_billing: true`, `skip_ci_when_actions_unavailable: true` (upgrade PRs only — **not** Dependabot), `auto_merge_dependabot: true`, `dependabot_auto_merge_levels: [patch, minor, major]`. Cadence: Monday Dependabot → Tuesday `argus-weekly` (14:00 UTC) on **`argus-runner` only** → optional **Tuesday Steward** for true judgment leftovers. Public product must not schedule `argus-weekly` (dispatch-only; see [RUNNER.md](RUNNER.md)).

### Free-tier Actions / no payment card

Paid GitHub Actions is **optional**. If free minutes are gone or jobs never start, do **not** buy a plan — run on This Computer:

```bash
python -m argus local-weekly --apply
# or: pwsh -File scripts/local-weekly.ps1
# or: argus merge-upgrades --allow-unarmed --actions-unavailable --fix --loop 4
```

`local-weekly` sets the free-tier path (`ARGUS_ACTIONS_UNAVAILABLE=1`): portfolio scan locally, then upgrade clear/merge **without** requiring remote CI. Auto-detect also watches zero-step failed workflow jobs on `argus-runner` / `Argus`. Ledger: `actions_unavailable`.

## Quiet posture (don’t bother the creator)

- One log line per run (`argus <family>: findings=… outcome=…`)
- No per-finding Issues / channel pings under YOLO
- Judgment leftovers → one private **yolo-digest** Issue
- Unprompted surfaces: `YOLO-OFF.md` / `GROK-OFF.md` and remote `main_red` only

## Hard floors (never lifted)

Same as [`docs/SAFETY.md`](SAFETY.md) / `safety.yaml`:

- `never_force_push`, `never_delete_repos`, `prefer_pull_requests`
- Every `auto_safe` / agent fix still needs an executable **gate**
- No secret / `.env` commits; no auto-archive; no Grok merges
- No force-close of human-authored PRs
- **Brand icons:** brief-only PR (`docs/BRAND_ICON_BRIEF.md`) — Argus never generates PNG assets

## Continuous zero

Goal: every armed YOLO run and every `argus local-weekly --apply` / vanilla `--apply` drives **mechanical open fixes toward zero** without a BUILD_PLAN punch list.

| Step | Config |
|------|--------|
| Auto `argus rules sync` when lock stale | `auto_rules_sync` (normal + yolo) |
| No portfolio fan-out of `RULES-STALE` / `SEC-RELEASE-TOKEN-MISSING` | signals in `argus/signals/contract.py` (controller-only; token opt-in `ARGUS_REQUIRE_RELEASE_TOKEN=1`) |
| Deterministic handlers | `normal.yolo_handlers` / `yolo.apply_api_handlers` |
| Soft-clear `CI-LATEST-FAILED` when Actions unavailable | `yolo.resolve_ci_when_actions_unavailable` |
| Rescore + re-apply once | `continuous_zero` / `second_pass` / `second_pass_if_budget` |

Steady state leftovers (digest / Steward only): brand artwork, park/archive judgment, Dependabot alert accept/dismiss after automation is enabled. Paying for Actions is never required.

## Pipeline loop

1. **Auto rules sync** when stale (continuous zero).
2. Batched discover + score (rate-limit aware).
3. `auto_safe` apply.
4. Deterministic handlers (`argus/yolo.py`) for agent + API-safe ids (`apply_api_handlers`).
5. Soft-resolve `CI-LATEST-FAILED` when Actions unavailable.
6. **Clear upgrade blockers** (YOLO mandatory): fix → wait → soft-merge loop on parent-upgrade PRs + Dependabot (all bump levels, CI must be green).
7. Squash-merge remaining `chore(argus)*` PRs (after six checks).
8. Health delta + apply history + action ledger (`dist/actions.jsonl`).
9. **Second pass** when budget remains.
10. One private **yolo-digest YYYY-MM-DD** Issue for judgment leftovers only.

## Handlers

| Fix id | Action |
|--------|--------|
| `SEC-CODEQL` | Code Scanning default setup |
| `SEC-OPEN-DEPENDABOT-ALERTS` | Enable automated security fixes |
| `BRAND-ICON-MISSING` | Judgment only (brief PR exists; no auto-clear of missing art) |
| `LINEAGE-RECOMMEND-UPGRADE` | Lineage bump PR |
| `AGENT-WHAT-NOT` / `AGENT-MEMORY-LAYOUT` | README / `.agent/` PRs |
| `PR-STALE` | Close bot/`chore/argus-*` idle PRs; nudge comment only on human PRs |
| `CI-LATEST-FAILED` | Soft-resolve when Actions unavailable; else digest (no invented patches) |
| `ISSUE-PATTERNED-AUTO` / `AGENT-STALE-ISSUES` | Close `argus-auto` / digest / bot bump Issues; nudge other stale human Issues (never invent product patches) |
| `BOARD-RESTRUCTURE` | Mechanical APB rebuild of divergent `BUILD_PLAN.md` (preserve open tasks; root board if it lived in `docs/`) |
| `HUMAN-PARK-INACTIVE` / `HUMAN-ARCHIVE-JUDGMENT` | Digest only (never archive) |

`BOARD-MARKERS` is `auto_safe` (append missing APB marker lanes + fold `## News inbox (synced)`). See [SAFETY.md](SAFETY.md) BUILD_PLAN format hygiene.

## Prefer Argus autoload over Grok mutators

Add or tighten fixes in `config/fixes*.yaml` with `auto_safe: true` and a real `gate` instead of teaching Grok to edit code. YOLO only accelerates what Argus already knows how to apply safely.
