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

## Rate limits

Authenticated GitHub REST **core = 5000 requests/hour**. Full portfolio scans cost ~50 calls/repo — see [`RATE_LIMIT.md`](RATE_LIMIT.md). Run `argus doctor` and wait if `remaining` is below `github_api.reserve`.

## Before / after health

Each `argus run` / `argus fix` writes:

- `dist/health-before.json` / `dist/health-after.json` / `dist/health.json`
- `dist/health-delta.md` (+ `.json`) — open-fix and attention deltas, PRs opened

Projected “after” removes auto_safe IDs that were applied (or would be, on dry-run). Scores on the default branch only improve after those PRs merge. HTML report banner includes the same delta.

Skip the public profile Overview repo:

```bash
argus fix --apply --skip-profile --no-notify
```

## After apply feels boring (optional YOLO)

1. Keep hard floors in `config/safety.yaml` (`never_force_push`, etc.).
2. Set `apply_mode: yolo` on the private runner only.
3. Enable GitHub auto-merge (or branch rules) so green Argus `auto_safe` / Dependabot PRs merge without a click (YOLO: all bump levels; vanilla `--apply`: patch+minor). CI must actually be green.
4. Leave release publishing and unlabeled product bugs human; Grok stays draft/digest ([GROK_BOTS.md](GROK_BOTS.md)).
5. Kill switch: `apply_mode: normal` + disable GitHub auto-merge.

Details: [YOLO.md](YOLO.md).
