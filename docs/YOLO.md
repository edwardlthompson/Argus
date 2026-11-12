# YOLO mode (hands-off — private runner only)

YOLO is Argus’s **private-runner apply policy**: gated `auto_safe` + mechanical handlers + squash-merge of Argus/Dependabot **patch** PRs in one loop. It is **not** “Grok can push anything.”

## Dual-plane (locked)

| Plane | YOLO |
|-------|------|
| **Public product / template** (`edwardlthompson/Argus`) | **Off** — `apply_mode: normal`, no `yolo.on` (vanilla still gets upgrade **fix/heal** on explicit `--apply`; merges stay human — see [SAFETY.md](SAFETY.md)) |
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
  skip_profile: true
  auto_merge_auto_safe: true
  auto_merge_dependabot_patch: true
  auto_dispatch_agents: true
  auto_merge_agent_prs: true
  max_auto_merges_per_day: 80
  max_yolo_actions_per_run: 100
  close_stale_bot_prs_days: 14
  stale_pr_idle_days: 30
  second_pass_if_budget: true
```

### YOLO implies apply

When YOLO is armed, `argus run` / `argus fix` **apply** unless you pass `--dry-run`. Pass `--with-profile` only if you intentionally want Overview mutations (default skips `YOU/YOU`).

## Six pre-merge checks

Before squash-merge: armed · hard floors · prefer PRs · title policy · CI green · not sacred profile.

## Parent upgrade merges

When `yolo.auto_merge_upgrade_prs: true` (default), YOLO also squash-merges open PRs titled `upgrade parent rules` on heads `chore/argus-upgrade-*` after CI is green (or no checks). Operator one-shot from a product clone:

```bash
argus fix-upgrades --allow-unarmed
argus merge-upgrades --allow-unarmed --fix --soft-allowlist --loop 10 --sleep 180
```

`--fix` / scheduled YOLO runs a **mandatory clear loop** (`clear_upgrade_blockers`): heal + mechanical fixers (markdown pipes, F-Droid stubs, ADR Status→Accepted, CodeQL android drop when pruned, conventional titles, **Trivy npm overrides + lockfile regen**) → wait for CI → soft-merge → repeat. Soft-merge is template/hygiene noise only (`Template Upgrade Simulation`, `Validate Bootstrap Artifacts`, Conventional Commits title, …; umbrella `CI` ignored). **Hard floors stay:** Security/Trivy/CodeQL/Gitleaks/Dependency Review/Scorecard and product Feature Gate/build/ADR/assemble failures never soft-merge — fixers must clear them or they stay on the digest. Expand `NPM_OVERRIDES` / `CAPACITOR_PINS` in `argus/yolo_trivy_npm.py` when new recurring CVEs appear.

**Hands-off defaults** (`config/safety.yaml` → `yolo`): `clear_upgrade_blockers: true`, `clear_upgrade_loops: 8`, `fix_upgrade_prs: true`, `soft_merge_upgrade_noise: true`, `auto_merge_upgrade_prs: true`, `merge_when_actions_billing: true`, `skip_ci_when_actions_unavailable: true`. Cadence: Monday Dependabot → Tuesday `argus-weekly` (14:00 UTC) on **`argus-runner` only** → optional **Tuesday Steward** for true judgment leftovers. Public product must not schedule `argus-weekly` (dispatch-only; see [RUNNER.md](RUNNER.md)).

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

## Pipeline loop

1. Batched discover + score (rate-limit aware).
2. `auto_safe` apply.
3. YOLO handlers (`argus/yolo.py`) for human/agent ids that are API-safe.
4. **Clear upgrade blockers** (mandatory): fix → wait → soft-merge loop on parent-upgrade PRs + Dependabot patches.
5. Squash-merge remaining `chore(argus)*` PRs (after six checks).
6. Health delta + apply history + action ledger (`dist/actions.jsonl`).
7. Optional **second pass** when budget remains.
8. One private **yolo-digest YYYY-MM-DD** Issue for hard leftovers only.

## Handlers

| Fix id | Action |
|--------|--------|
| `SEC-CODEQL` | Code Scanning default setup |
| `SEC-OPEN-DEPENDABOT-ALERTS` | Enable automated security fixes |
| `BRAND-ICON-MISSING` | Design brief PR only (no generated asset) |
| `LINEAGE-RECOMMEND-UPGRADE` | Lineage bump PR |
| `AGENT-WHAT-NOT` / `AGENT-MEMORY-LAYOUT` | README / `.agent/` PRs |
| `PR-STALE` | Close bot/`chore/argus-*` idle PRs; nudge comment only on human PRs |
| `CI-LATEST-FAILED` | Digest only (no invented patches) |
| `HUMAN-PARK-INACTIVE` / `HUMAN-ARCHIVE-JUDGMENT` | Digest only (never archive) |

## Prefer Argus autoload over Grok mutators

Add or tighten fixes in `config/fixes*.yaml` with `auto_safe: true` and a real `gate` instead of teaching Grok to edit code. YOLO only accelerates what Argus already knows how to apply safely.
