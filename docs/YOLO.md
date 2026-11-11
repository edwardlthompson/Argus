# YOLO mode (hands-off — private runner only)

YOLO is Argus’s **private-runner apply policy**: gated `auto_safe` + mechanical handlers + squash-merge of Argus/Dependabot **patch** PRs in one loop. It is **not** “Grok can push anything.”

## Dual-plane (locked)

| Plane | YOLO |
|-------|------|
| **Public product / template** (`edwardlthompson/Argus`) | **Off** — `apply_mode: normal`, no `yolo.on` |
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

`--fix` runs heal plus mechanical fixers (markdown table pipes, F-Droid changelog stubs). `--soft-allowlist` squash-merges when the only remaining failures are template noise (`Template Upgrade Simulation`, `Validate Bootstrap Artifacts`, …; umbrella `CI` ignored). Security/Trivy/CodeQL/Gitleaks/Dependency Review and product Feature Gate/build failures still block.

**Hands-off defaults** (`config/safety.yaml` → `yolo`): `fix_upgrade_prs: true`, `soft_merge_upgrade_noise: true`, `auto_merge_upgrade_prs: true`. Scheduled YOLO on the private runner runs fix → soft-merge upgrades without an operator flag. Cadence: Monday Dependabot → Tuesday `argus-weekly` (14:00 UTC) on **`argus-runner` only** → optional **Tuesday Steward** Grok digest ([GROK_BOTS.md](GROK_BOTS.md)). Public product must not schedule `argus-weekly` (dispatch-only; see [RUNNER.md](RUNNER.md)).

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
4. Squash-merge `chore(argus)*` PRs + Dependabot **patch/minor** PRs (after six checks).
5. Health delta + apply history + action ledger (`dist/actions.jsonl`).
6. Optional **second pass** when budget remains.
7. One private **yolo-digest YYYY-MM-DD** Issue for leftovers.

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
