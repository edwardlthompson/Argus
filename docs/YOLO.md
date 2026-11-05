# YOLO mode (hands-off)

YOLO is Argus’s **private-runner apply policy**: gated `auto_safe` + mechanical handlers + squash-merge of Argus/Dependabot **patch** PRs in one loop. It is **not** “Grok can push anything.”

See [`docs/GROK_BOTS.md`](GROK_BOTS.md) and [ADR 0001](adr/0001-grok-bots-draft-digest-and-yolo.md).

## Config

[`config/safety.yaml`](../config/safety.yaml):

```yaml
apply_mode: yolo   # normal | yolo

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

Shipped product default is **`apply_mode: yolo`** for the private controller. Kill switch: set `apply_mode: normal`.

### YOLO implies apply

When `apply_mode: yolo`, `argus run` / `argus fix` **apply** unless you pass an explicit `--dry-run`. You do not need a separate “remember apply=true” step. Pass `--with-profile` only if you intentionally want Overview mutations (default skips `YOU/YOU`).

## Hard floors (never lifted)

Same as [`docs/SAFETY.md`](SAFETY.md) / `safety.yaml`:

- `never_force_push`, `never_delete_repos`, `prefer_pull_requests`
- Every `auto_safe` / agent fix still needs an executable **gate**
- No secret / `.env` commits; no auto-archive; no Grok merges
- No force-close of human-authored PRs

## Pipeline loop

1. Batched discover + score (rate-limit aware).
2. `auto_safe` apply.
3. YOLO handlers (`argus/yolo.py`) for human/agent ids that are API-safe.
4. Squash-merge `chore(argus)*` PRs + Dependabot **patch/minor** PRs.
5. Health delta + apply history + shareable portfolio HTML/MD (`dist/` + private `argus-history/reports/`).
6. Optional **second pass** in-process when budget remains and YOLO-eligible work is left.
7. One private **yolo-digest YYYY-MM-DD** Issue for leftovers (CI judgment, park/archive candidates, human stale PRs).

## Handlers

| Fix id | Action |
|--------|--------|
| `SEC-CODEQL` | Code Scanning default setup |
| `SEC-OPEN-DEPENDABOT-ALERTS` | Enable automated security fixes |
| `BRAND-ICON-MISSING` | PNG PR |
| `LINEAGE-RECOMMEND-UPGRADE` | Lineage bump PR |
| `AGENT-WHAT-NOT` / `AGENT-MEMORY-LAYOUT` | README / `.agent/` PRs |
| `PR-STALE` | Close bot/`chore/argus-*` idle PRs; nudge comment only on human PRs |
| `CI-LATEST-FAILED` | Digest only (no invented patches) |
| `HUMAN-PARK-INACTIVE` / `HUMAN-ARCHIVE-JUDGMENT` | Digest only (never archive) |

## Workload under YOLO

| Work | Who |
|------|-----|
| Hygiene `auto_safe` | Argus PR → squash-merge |
| Dependabot **patch/minor** | Squash-merge; majors stay human |
| Stale bot / `chore/argus-*` PRs | Close after idle days |
| Stale human PRs | Nudge + digest |
| CI red / park / archive | Digest Issue only |
| Profile Overview | Skipped when `skip_profile: true` |

## Prefer Argus autoload over Grok mutators

Add or tighten fixes in `config/fixes*.yaml` with `auto_safe: true` and a real `gate` instead of teaching Grok to edit code. YOLO only accelerates what Argus already knows how to apply safely.
