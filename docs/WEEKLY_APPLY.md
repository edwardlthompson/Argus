# First weekly `--apply` runbook

Operator checklist for turning on auto-fix on the **private runner**.

1. Confirm runner is private and `config/inbox.yaml` has `controller_repo: YOU/argus-runner`, `security_issues: true`.
2. Actions → **argus-scan** → Run workflow → `apply=false`, `notify=false`.
3. Download artifact `argus-scan-dist`. Open `report.html` / `inbox.json`. Confirm repos look right.
4. Optional: set Discord/Telegram secrets; re-run with `notify=true`, `apply=false` once.
5. Actions → **argus-scan** → `apply=true`. Expect:
   - `auto_safe` PRs on targets (topics, hygiene files, lineage, profile README when due)
   - Issues with `argus-inbox` for human Settings tasks
6. Phone: clear Issues (close or comment `argus done`).
7. Leave **argus-weekly** on cron with `apply` input only when you trust the dry-runs (or keep weekly dry-run and use scan for apply).

Halt and open an Issue on the runner if apply opens unexpected PRs — tighten `config/allowlist.yaml` / `safety.yaml`.
