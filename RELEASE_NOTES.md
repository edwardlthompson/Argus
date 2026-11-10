# Release notes — Argus 0.6.0

## Highlights

- **Hands-off upgrade YOLO** — Scheduled runs fix + soft-merge parent-upgrade PRs (`fix_upgrade_prs`, `soft_merge_upgrade_noise`). Operator CLI: `argus fix-upgrades` / `merge-upgrades --fix --soft-allowlist`.
- **Tuesday cadence** — `argus-weekly` cron moved to **Tuesday 14:00 UTC** (after Monday Dependabot). Sync `weekly.yml` to private `argus-runner`.
- **Tuesday Steward** — Grok digest skill + `argus grok pack tuesday-steward` one-paste bootstrap (no create-Bot API). Optional webhook after weekly.
- **Health infographic** — Every scan writes `dist/health-infographic.svg|.html` and `health-hotspots.json` (hottest fix ids / repos before→after).

## Upgrade notes

- Re-bootstrap or copy `config/safety.yaml` YOLO flags onto the **private runner** only.
- Paste `dist/grok-bots/tuesday-steward-bootstrap.md` into Grok once; set `GROK_STEWARD_WEBHOOK_*` on the runner if you want auto-ping.
- Security/Trivy/CodeQL/Feature Gate leftovers still need human judgment — soft-merge never bypasses those.

See `CHANGELOG.md` for the full list.
