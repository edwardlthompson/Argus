# Release notes — Argus 0.8.0

## Highlights

- **Continuous zero** — `--apply` / `local-weekly --apply` / armed YOLO auto-syncs rules, runs deterministic handlers, soft-clears CI when Actions is unavailable, and second-passes toward zero open Argus fixes.
- **Patterned Issue triage** — closes `argus-auto` / digest / bot bump Issues; nudges other stale human Issues (never invents product patches).
- **Report urgency** — Priority / Rest of fleet sorted by GitHub Issues (most first); green + zero-Issue repos omitted.
- **Signal honesty** — `RULES-STALE` and `SEC-RELEASE-TOKEN-MISSING` no longer fan out across the portfolio.

## Upgrade notes

- Free-tier: keep using `argus local-weekly --apply` (no payment card).
- Label Issues `argus-auto` when Argus should close them on the next apply.
- Public Pages stay sanitized (`docs/index.html`); full reports stay private.

See `CHANGELOG.md` for the full list.
