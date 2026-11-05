# Safety

## What Argus will never do

- Force-push or rewrite git history on a target repository
- Hard-delete a GitHub repository
- Auto-apply judgment-heavy or low-confidence changes
- Run LLMs inside scoring or runbook composition
- Bypass dry-run in CI without an explicit opt-in
- **Publish per-repo security gaps on public Pages** (missing Dependabot, secret scanning, CodeQL, CVE lists, or “how to enable” checklists)

## Public vs private surfaces

| Surface | Allowed content |
|---------|-----------------|
| GitHub Pages (public) | Status counts only (`status.html`) — last run, human task count, quiet/needs-you |
| Actions artifacts | Full `report.html`, `runbook.md`, `inbox.json` (repo ACL) |
| Chat (Discord/Telegram) | Counts + deep links to Issues / Actions — no CVE titles or “secret scanning off on X” |
| GitHub Issues (`argus-inbox`) | Non-security human grandma steps by default. Security-class (`SEC-*`) stays in artifacts until `config/inbox.yaml` sets `security_issues: true` (recommended only if the controller repo is **private**) |

Strongest posture: make `edwardlthompson/Argus` (or your fork) **private** so Issues, artifacts, and Actions inherit private ACL.

## Blast radius controls

| Control | Default |
|---------|---------|
| Allow-list mode | `owner_only` |
| Max auto PRs / run | 5 |
| Max concurrent agent sessions | 1 |
| Prefer PRs over direct commits | yes |
| Report-only on third-party targets | forced |
| Pages detail | status-only |
| Security Issues bodies | off (`security_issues: false`) |

Edit `config/safety.yaml`, `config/allowlist.yaml`, and `config/inbox.yaml` to tighten further.

## Permissions

Minimum for report-only: a token that can read the target repositories (public repos may work without a token subject to rate limits).

For auto-apply: write access to targets, or a GitHub App installation with contents + pull requests.

For Issues inbox sync on apply: `issues: write` on the controller (weekly/scan workflows already request it). Prefer a fine-grained `ARGUS_GITHUB_TOKEN` when cross-repo apply is needed.

When permissions are missing, Argus degrades to report-only for that repo and records the reason in artifacts / apply skip list.

## Circuit breaker

If agent gates fail repeatedly, agentic dispatch pauses and notifications fire so a human can inspect.
