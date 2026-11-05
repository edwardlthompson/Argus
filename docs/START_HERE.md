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

6. Open `dist/report.html` in a browser. If Argus needs you, the page lists grandma-simple steps.

## Weekly silence

Use `.github/workflows/weekly.yml` (already included). It runs `argus run --dry-run` by default until you flip the workflow input or secret to allow apply.

## Publish the HTML report (optional)

1. In the GitHub repo: **Settings → Pages → Source → GitHub Actions**.
2. Run the **pages** workflow (or wait for a successful weekly run).
3. Your grandma-friendly report will be at `https://<user>.github.io/<repo>/`.
4. Put that URL in notifications as `ARGUS_REPORT_URL` / `--report-url`.

## Enable notifications

1. Pick one channel in `.env` (preferred) or `config/notifications.yaml`:
   - Discord: `ARGUS_DISCORD_WEBHOOK=<webhook url>`
   - Telegram: `ARGUS_TELEGRAM_BOT_TOKEN` + `ARGUS_TELEGRAM_CHAT_ID`
   - Generic: `ARGUS_WEBHOOK_URL`
2. Set `ARGUS_REPORT_URL` to your Pages report URL.
3. Run **without** `--no-notify`: `argus run --dry-run --report-url "$ARGUS_REPORT_URL"`.
4. For Actions: add the same values as repository secrets/variables; weekly workflow already passes them.

Silent by default — you are only pinged for human tasks, critical security, or a failed run.

## Auto-fix without paste

```bash
argus fix                 # dry-run what would change
argus fix --apply         # apply auto_safe (topics, files, lineage bumps) via API/PRs
argus fix --apply --agent # also batch agent worktrees / mechanical fallback
```

Archived repos are skipped unless you pass `--include-archived`.

## Next reading

- [FORKING.md](FORKING.md) — point Argus at *your* account
- [SAFETY.md](SAFETY.md) — what Argus will never do
- [GRANDMA_MODE.md](GRANDMA_MODE.md) — how human instructions are written
- [THIRD_PARTY.md](THIRD_PARTY.md) — report on someone else’s repos
