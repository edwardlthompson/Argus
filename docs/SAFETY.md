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
| `normal` (default) | Dry-run or `apply=true` opens `auto_safe` PRs; **human merges** |
| `yolo` | Same apply path, but policy prefers **auto-merge** when gate + required CI are green (Dependabot **patch** optional). Kill switch: set `apply_mode: normal` |

Hard floors above still apply under YOLO. Grok Bots never merge — see [`GROK_BOTS.md`](GROK_BOTS.md) and [`YOLO.md`](YOLO.md). Prefer new Argus `auto_safe` matchers over LLM mutators.

## Permissions

- Report-only: read token (or public rate limits).
- Auto-apply: write to targets (contents + pull requests).
- Inbox sync: `issues: write` on the **private** controller.
- Profile README: write to public `YOU/YOU`.

Prefer fine-grained `ARGUS_GITHUB_TOKEN` on the private runner only.

## Circuit breaker

If agent gates fail repeatedly, agentic dispatch pauses and notifications fire so a human can inspect.
