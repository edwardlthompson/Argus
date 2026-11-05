# Release notes — Argus 0.4.0

## Highlights

- **Hands-off YOLO** — `apply_mode: yolo` applies gated fixes, merges `chore(argus)` + Dependabot **patch** PRs, closes stale bot PRs, optional in-process second pass, and opens one private `yolo-digest` Issue for judgment leftovers. Profile Overview stays sacred (`skip_profile`).
- **Shareable portfolio reports** — Dark (default) / light HTML with charts + theme toggle; matching Markdown; dated copies under private `argus-history/reports/`.
- **Health + rate limits** — Before/after health deltas every run; GitHub core budget pacing, wait-until-reset, batched discovery (`docs/RATE_LIMIT.md`).
- **Apply history** — Append-only local + private-runner `argus-history/` sync.
- **Grok Bots pack** — Draft/digest skills only; Argus remains the sole mutator (ADR 0001).

## Upgrade notes

- Private runner: leave `apply_mode: yolo` or set `normal` as kill switch. Weekly/scan with unset apply follows safety.yaml (YOLO implies apply); pass `apply=false` for explicit dry-run.
- Expect Actions minute burn from mass merges + CodeQL; thin CI on `argus-history/**` pushes if minutes are tight.
- Prefer `python scripts/agent-run.py verify` before merge. Template Release Please / full pre-release-gate remain N/A (G12).

See `CHANGELOG.md` for the full list.
