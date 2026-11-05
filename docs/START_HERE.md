# Start here

Argus watches your GitHub repositories, scores hygiene, auto-applies only safe fixes, and tells you — in plain language — when a human is needed.

## 5-minute setup

1. Fork or clone this repository.
2. Copy `.env.example` to `.env` and set `GITHUB_TOKEN` (a classic PAT with `repo` scope, or a fine-grained token that can read your repos).
3. Create a virtualenv and install:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

4. Check configuration:

```bash
argus doctor
```

5. Dry-run against your own account:

```bash
argus run --dry-run
```

6. Open `dist/report.html` locally (full detail). Public Pages only publish `status.html` counts — never the exploit map.

## Private control plane (day-to-day)

1. **Human inbox** — On apply runs, Argus opens/updates Issues on the controller with label `argus-inbox`. Close the issue or comment `argus done` when finished. Security-class tasks (`SEC-*`) stay out of public Issue bodies by default (`config/inbox.yaml` → `security_issues: false`); details live in the Actions artifact.
2. **Full report** — Download the `argus-dist` / `argus-scan-dist` artifact from Actions (`report.html`, `runbook.md`, `inbox.json`). Retention: 30 days.
3. **Notifications** — Discord/Telegram get “Argus needs you for N tasks” plus links to the inbox and the Actions run. No CVE titles in chat.
4. **Start a scan** — Actions → **argus-scan** → Run workflow (mobile-friendly). Weekly schedule remains in **argus-weekly**.
5. **Public status (optional)** — Pages shows last-run counts only. Set `ARGUS_REPORT_URL` to that status URL if you want it in digests.

Recommend making the controller repo **private** for the strongest ACL on Issues + artifacts.

## Weekly silence

Use `.github/workflows/weekly.yml`. It runs `argus run --dry-run` by default until you flip the workflow input to allow apply (which also writes Issues).

## Enable notifications

1. Pick one channel in `.env` (preferred) or `config/notifications.yaml`:
   - Discord: `ARGUS_DISCORD_WEBHOOK=<webhook url>`
   - Telegram: `ARGUS_TELEGRAM_BOT_TOKEN` + `ARGUS_TELEGRAM_CHAT_ID`
   - Generic: `ARGUS_WEBHOOK_URL`
2. Optional: set `ARGUS_REPORT_URL` to the public **status** Pages URL.
3. Run **without** `--no-notify`: `argus run --dry-run --report-url "$ARGUS_REPORT_URL"`.
4. For Actions: add the same values as repository secrets/variables; weekly/scan workflows already pass them.

Silent by default — you are only pinged for human tasks, critical security scores, or a failed run.

## Auto-fix without paste

```bash
argus fix                 # dry-run what would change
argus fix --apply         # apply auto_safe (topics, files, lineage bumps) via API/PRs
argus fix --apply --agent # also batch agent worktrees / mechanical fallback
```

Archived repos are skipped unless you pass `--include-archived`.

## Next reading

- [FORKING.md](FORKING.md) — point Argus at *your* account
- [SAFETY.md](SAFETY.md) — what Argus will never do (including public Pages)
- [GRANDMA_MODE.md](GRANDMA_MODE.md) — how human instructions are written
- [THIRD_PARTY.md](THIRD_PARTY.md) — report on someone else’s repos
- [PUBLISH.md](PUBLISH.md) — push controller + enable Actions/Pages
