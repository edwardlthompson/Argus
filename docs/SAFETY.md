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
| `normal` (default / **vanilla**) | Dry-run safe. Explicit `--apply` / `local-weekly --apply` runs **continuous zero**: `auto_safe` PRs, deterministic handlers, auto rules sync, second pass. **Human merges** on public product. |
| `yolo` | Continuous zero + auto-merge when gate + CI policy allow. Kill switch: set `apply_mode: normal` / delete `yolo.on`. |

### Continuous zero (config)

Behaviour in `config/safety.yaml`:

- `normal.yolo_handlers` / `normal.auto_rules_sync` / `normal.continuous_zero` / `normal.second_pass`
- `yolo.apply_api_handlers` / `yolo.auto_rules_sync` / `yolo.resolve_ci_when_actions_unavailable` / `yolo.continuous_zero`

Controller-only signals (`RULES-STALE`, opt-in `SEC-RELEASE-TOKEN-MISSING`) never fan out to the portfolio. Judgment leftovers (brand art, park/archive, residual Dependabot accept/dismiss) stay on the private digest — see [`YOLO.md`](YOLO.md).

### YOLO → vanilla (what is safe)

| Capability | Vanilla (`normal` + `--apply`) | YOLO (armed) |
|------------|--------------------------------|--------------|
| `auto_safe` PRs (gated) | yes | yes |
| Upgrade PR mechanical fix/heal | yes (`normal.fix_upgrade_prs`) | yes |
| Free-tier Actions skip / `local-weekly` | yes (CLI opt-in) | yes (scheduled) |
| Soft-merge allowlist / clear loop | no (use `merge-upgrades --allow-unarmed`) | yes |
| Auto-merge upgrades / Dependabot patch | no (human or CLI) | yes |
| Deterministic API handlers (CodeQL, lineage, …) | yes (`normal.yolo_handlers`) | yes (`apply_api_handlers`) |
| Auto rules sync when stale | yes | yes |
| Soft-resolve `CI-LATEST-FAILED` when Actions down | yes (via handlers cfg) | yes |
| Second pass / quiet yolo-digest | yes (`continuous_zero`) | yes |
| Imply apply without `--apply` | no | yes |

Hard floors above still apply under YOLO. Grok Bots never merge — see [`GROK_BOTS.md`](GROK_BOTS.md) and [`YOLO.md`](YOLO.md). Prefer new Argus `auto_safe` matchers over LLM mutators.

## Permissions

- Report-only: read token (or public rate limits).
- Auto-apply: write to targets (contents + pull requests).
- Inbox sync: `issues: write` on the **private** controller.
- Profile README: write to public `YOU/YOU`.

Prefer fine-grained `ARGUS_GITHUB_TOKEN` on the private runner only.

## Circuit breaker

If agent gates fail repeatedly, agentic dispatch pauses and notifications fire so a human can inspect.
