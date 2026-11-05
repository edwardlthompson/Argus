# Safety

## What Argus will never do

- Force-push or rewrite git history on a target repository
- Hard-delete a GitHub repository
- Auto-apply judgment-heavy or low-confidence changes
- Run LLMs inside scoring or runbook composition
- Bypass dry-run in CI without an explicit opt-in

## Blast radius controls

| Control | Default |
|---------|---------|
| Allow-list mode | `owner_only` |
| Max auto PRs / run | 5 |
| Max concurrent agent sessions | 1 |
| Prefer PRs over direct commits | yes |
| Report-only on third-party targets | forced |

Edit `config/safety.yaml` and `config/allowlist.yaml` to tighten further.

## Permissions

Minimum for report-only: a token that can read the target repositories (public repos may work without a token subject to rate limits).

For auto-apply: write access to targets, or a GitHub App installation with contents + pull requests.

When permissions are missing, Argus degrades to report-only for that repo and records the reason in artifacts / apply skip list.

## Circuit breaker

If agent gates fail repeatedly, agentic dispatch pauses and notifications fire so a human can inspect.
