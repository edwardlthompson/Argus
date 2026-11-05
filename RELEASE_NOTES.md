# Release notes — Argus 0.3.0

## Highlights

- **Dual plane shipped** — Public MIT product + private `argus-runner` bootstrap; doctor guards against public security Issues.
- **Profile Overview** — `PROF-README` PRs to `USER/USER` from live languages/topics + YAML voice.
- **Operator loop** — Projects v2 inbox sync, chat `repository_dispatch` scan, quiet hours / digest coalesce, `argus explain` / `inbox` / `status --safe`.
- **Auto-safe expansion** — CODEOWNERS, `.gitignore`, CodeQL pack, Dependabot/secret-scan API toggles, dry-run `would_prs`, per-owner PR caps.
- **Security CI** — CodeQL, gitleaks, SBOM on release, pinned Action SHAs, project-scoped `update-deps` + pip-audit.

## Upgrade notes

- Point private runner `config/inbox.yaml` at `YOU/argus-runner`; keep `security_issues: false` on public Argus.
- Optional: set `project_number` for Projects v2 sync; wire Discord/Telegram bots to `repository_dispatch` with a server-side PAT.
- Prefer `python scripts/agent-run.py verify` before merge.

See `CHANGELOG.md` for the full list.
