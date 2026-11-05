# Start here

Argus watches your GitHub repositories, scores hygiene, auto-applies only safe fixes, and tells you — in plain language — when a human is needed.

## Dual plane (read this once)

| Repo | Role |
|------|------|
| **Public Argus** | MIT source, docs, CI tests, optional status-only Pages |
| **Private `argus-runner`** | Scheduled scan, `--apply`, Issues inbox, full artifacts, secrets |
| **Public `YOU/YOU`** | Profile Overview README (updated via Argus PR) |

Never publish per-repo security gaps on the public product.

## 5-minute operator setup

1. Clone the public product.
2. Bootstrap the private runner:

```bash
pwsh -File scripts/bootstrap-argus-runner.ps1
# or: bash scripts/bootstrap-argus-runner.sh
```

3. Optional local install for doctor/debug:

```bash
python -m venv .venv
pip install -e ".[dev]"
cp .env.example .env   # GITHUB_TOKEN=
argus doctor
```

4. On the private runner: Actions → **argus-scan** (dry-run first), then `apply=true` when ready.
5. Phone workflow: Issues labeled `argus-inbox` + artifact download.

## Private control plane (day-to-day)

1. **Inbox** — Issues on the **private runner** (`argus-inbox`). Close or comment `argus done`. With `security_issues: true` on a private controller, SEC-* grandma steps may appear in Issues.
2. **Full report** — Actions artifact (`report.html`, `runbook.md`, `inbox.json`), ~30 days.
3. **Notifications** — counts + links to inbox/Actions (no CVE titles in chat).
4. **Scan** — **argus-scan** / **argus-weekly** on the private runner.
5. **Public status (optional)** — product Pages counts only.

## Profile Overview

When enabled, Argus opens a PR on public `YOU/YOU` with a text-first README (About, capabilities, stack from live languages/topics). **Featured projects** are public non-fork repos ranked by **stars, then traffic** (views + clones), with **app icons** (repo `icon.png` / `logo.png` / fastlane icon when present, else Open Graph). GitHub pin choices stay private/operator-only — never published on the Overview README. Marker: `<!-- argus:profile-readme -->`.

## Notifications

Prefer `.env` secrets: `ARGUS_DISCORD_WEBHOOK`, Telegram pair, or `ARGUS_WEBHOOK_URL`. Optional `ARGUS_REPORT_URL` = status-only URL.

## Auto-fix without paste

```bash
argus fix                 # dry-run
argus fix --apply         # auto_safe via API/PRs
argus fix --apply --agent # optional agent batches (local)
```

Archived repos skipped unless `--include-archived`.

## Next reading

- [FORKING.md](FORKING.md) · [PUBLISH.md](PUBLISH.md) · [RUNNER.md](RUNNER.md) · [WEEKLY_APPLY.md](WEEKLY_APPLY.md)
- [SAFETY.md](SAFETY.md) · [THREAT_MODEL.md](THREAT_MODEL.md) · [FIRST_30_DAYS.md](FIRST_30_DAYS.md) · [GRANDMA_MODE.md](GRANDMA_MODE.md)
