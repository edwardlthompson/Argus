# Safety

## What Argus will never do

- Force-push or rewrite git history on a target repository
- Hard-delete a GitHub repository
- Auto-apply judgment-heavy or low-confidence changes
- Run LLMs inside scoring or runbook composition
- Bypass dry-run in CI without an explicit opt-in
- **Publish per-repo security gaps on public Pages or a public product Issues inbox**

## Dual-plane surfaces

| Surface | Visibility | Allowed content |
|---------|------------|-----------------|
| Public product repo | Public | Source, docs, CI; status-only Pages counts |
| Private runner | Private | Full report artifacts, Issues inbox, apply, secrets |
| Chat digests | Private channels | Counts + deep links — no CVE / “secret scanning off on X” |
| Profile `YOU/YOU` | Public | Marketing Overview README from live languages/projects + YAML voice — not security gaps |

`security_issues: true` only when `controller_repo` is **private**. `argus doctor` warns if you enable security Issue bodies against a public controller.

## Blast radius controls

| Control | Default |
|---------|---------|
| Allow-list mode | `owner_only` |
| Max auto PRs / run | 5 |
| Max concurrent agent sessions | 1 |
| Prefer PRs over direct commits | yes |
| Report-only on third-party targets | forced |
| Pages detail | status-only |
| Security Issues bodies | off on public examples |

Edit `config/safety.yaml`, `config/allowlist.yaml`, and `config/inbox.yaml` to tighten further.

## Apply modes

| Mode | Behavior |
|------|----------|
| `normal` (default / **vanilla**) | Dry-run safe. Explicit `--apply` / `local-weekly --apply` runs **continuous zero**: `auto_safe` PRs, deterministic handlers, auto rules sync, second pass, **Dependabot patch+minor** squash-merge after CI is actually green. Upgrade merges stay human on public product. |
| `yolo` | Continuous zero + auto-merge when gate + CI policy allow, including **all Dependabot bump levels**. Kill switch: set `apply_mode: normal` / delete `yolo.on`. |

### Continuous zero (config)

Behaviour in `config/safety.yaml`:

- `normal.yolo_handlers` / `normal.auto_rules_sync` / `normal.continuous_zero` / `normal.second_pass` / `normal.merge_dependabot` + `dependabot_auto_merge_levels`
- `yolo.apply_api_handlers` / `yolo.auto_rules_sync` / `yolo.resolve_ci_when_actions_unavailable` / `yolo.continuous_zero` / `yolo.auto_merge_dependabot` + `dependabot_auto_merge_levels`

Controller-only signals (`RULES-STALE`, opt-in `SEC-RELEASE-TOKEN-MISSING`) never fan out to the portfolio. Judgment leftovers (brand art, park/archive, residual Dependabot accept/dismiss) stay on the private digest — see [`YOLO.md`](YOLO.md).

### YOLO → vanilla (what is safe)

| Capability | Vanilla (`normal` + `--apply`) | YOLO (armed) |
|------------|--------------------------------|--------------|
| `auto_safe` PRs (gated) | yes | yes |
| Upgrade PR mechanical fix/heal | yes (`normal.fix_upgrade_prs`) | yes |
| Free-tier Actions skip / `local-weekly` | yes (CLI opt-in) | yes (scheduled) |
| Soft-merge allowlist / clear loop | no (use `merge-upgrades --allow-unarmed`) | yes |
| Auto-merge upgrades | no (human or CLI) | yes |
| Auto-merge Dependabot (CI green required) | patch+minor (`normal.dependabot_auto_merge_levels`) | all levels including major |
| Deterministic API handlers (CodeQL, lineage, …) | yes (`normal.yolo_handlers`) | yes (`apply_api_handlers`) |
| Auto rules sync when stale | yes | yes |
| Soft-resolve `CI-LATEST-FAILED` when Actions down | yes (via handlers cfg) | yes |
| Second pass / quiet yolo-digest | yes (`continuous_zero`) | yes |
| Overview sync (stars/views/icons/membership) | yes (`normal.sync_profile`) | yes (`yolo.sync_profile`; `skip_profile` only blocks YOU/YOU auto_safe) |
| Imply apply without `--apply` | no | yes |

Hard floors above still apply under YOLO. Grok Bots never merge — see [`GROK_BOTS.md`](GROK_BOTS.md) and [`YOLO.md`](YOLO.md). Prefer new Argus `auto_safe` matchers over LLM mutators.

### Dependabot auto-merge (mode-aware)

Both vanilla `--apply` and YOLO squash-merge Dependabot PRs only after `evaluate_pre_merge` (same six checks as other Argus merges). **CI must actually be green.** `yolo.skip_ci_when_actions_unavailable` and billing/soft-allowlist skips apply to parent-upgrade merges, not dependency bumps — if checks never started, the PR stays open.

| Key | Vanilla (`normal`) | YOLO |
|-----|--------------------|------|
| Enable | `merge_dependabot` (alias `merge_dependabot_patch`) | `auto_merge_dependabot` (alias `auto_merge_dependabot_patch`) |
| Levels | `dependabot_auto_merge_levels: [patch, minor]` | `dependabot_auto_merge_levels: [patch, minor, major]` |

### BUILD_PLAN format hygiene

Portfolio boards are normalized toward agent-project-bootstrap `BUILD_PLAN_TEMPLATE.md`. This is **format hygiene**, not filing findings as chores:

| Fix | Class | Does |
|-----|-------|------|
| `BOARD-MARKERS` | `auto_safe` | Append missing marker lanes (`remaining-tally`, `local-agent-lane`, `cloud-agent-lane`, `open-prs-sync`, `template-gaps-sync`); fold `## News inbox (synced)` into lanes |
| `BOARD-RESTRUCTURE` | `agent` | Rebuild divergent boards to APB shape; preserve every open task + completed history; root `BUILD_PLAN.md` when the board lived in `docs/` |

Locator: root `BUILD_PLAN.md`, else `docs/BUILD_PLAN.md`. Gates are executable (markers present). PRs on `chore/argus-*`. See [`YOLO.md`](YOLO.md).

## Permissions

- Report-only: read token (or public rate limits).
- Auto-apply: write to targets (contents + pull requests).
- Inbox sync: `issues: write` on the **private** controller.
- Profile README: write to public `YOU/YOU`.

Prefer fine-grained `ARGUS_GITHUB_TOKEN` on the private runner only.

## Circuit breaker

If agent gates fail repeatedly, agentic dispatch pauses and notifications fire so a human can inspect.
