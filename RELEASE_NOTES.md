# Release notes — Argus 0.7.0

## Highlights

- **Free-tier Actions path** — `argus local-weekly` and `skip_ci_when_actions_unavailable`; paying for Actions is never required.
- **Sanitized portfolio Pages** — public `portfolio-pages.html` (metrics + graphs only). Full weakness reports stay private under `argus-history/reports/latest*`.
- **Tuesday Steward brief** — private `steward-brief.html` for Grok; never published to Pages.
- **Vanilla `--apply`** — upgrade fix/heal without arming YOLO; merges stay human unless you opt into CLI merge.

## Upgrade notes

- Point `ARGUS_REPORT_URL` at the **sanitized** Pages URL only.
- Full report / Steward brief: private runner `argus-history/reports/latest.html` and `latest-steward.html`.
- Enable GitHub Pages from `/docs` on public Argus (or Actions `pages` workflow when minutes allow).

See `CHANGELOG.md` for the full list.
