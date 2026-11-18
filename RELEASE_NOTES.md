# Release notes — Argus 0.9.0

## Highlights

- **Weekly Overview refresh** — every apply / Tuesday weekly / `local-weekly` refreshes `YOU/YOU` stars, forks, watches, Insights views, full icon rescan, and public↔private membership (`sync_profile`; independent of `skip_profile`).
- **Fleet report** — one table of every active repo (Issues → open PRs), attention bar in the last column; Overall Assessment at the bottom. Issues and PRs stay separate (GitHub’s issue count wrongly includes PRs).
- **Honest Issues vs PRs** — Priority/Fleet no longer treat open PRs as Issues.

## Upgrade notes

- Tuesday `argus-weekly` / `local-weekly` pass `--with-profile` so Overview stays current.
- `yolo.skip_profile` still blocks auto_safe/merge *into* Overview; set `sync_profile: false` or `--skip-profile` only if you want to pause the README PR.
- Free-tier: keep using `argus local-weekly --apply` (no payment card).

See `CHANGELOG.md` for the full list.
