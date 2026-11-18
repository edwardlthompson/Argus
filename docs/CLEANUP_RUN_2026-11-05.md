# Portfolio cleanup summary (2026-11-05)

Profile Overview (`edwardlthompson/edwardlthompson`) was **skipped** (`--skip-profile`).

## Before (dry-run baseline)

| Metric | Value |
|--------|-------|
| Repos scanned | 31 |
| Open fixes | **195** |
| Auto-safe | **67** |
| Human | 63 |
| Agent | 65 |
| Mean attention | 25.0 |
| Max attention | 42.8 |

Artifacts: `dist/cleanup-before.json`, dry-run log `dist/cleanup-dry-run.json.txt`.

## Fixes made (two `--apply` passes)

- **Pass 1:** 40 auto_safe actions applied (topics, descriptions, CODEOWNERS, CodeQL, Dependabot enable, secret scanning, lineage version bumps, etc.).
- **Pass 2:** 18 more applied.
- **~58** auto_safe items resolved in Argus state / PRs or direct API updates.
- Several `LINEAGE-MISSING-MARKERS` hit “PR already exists” (open `chore/argus-lineage-missing-markers`); apply now treats that 422 as success.
- Profile README: **not touched**.

Logs: `dist/cleanup-apply-1.json.txt`, `dist/cleanup-apply-2.json.txt`.

## After (projected after pass 2)

| Metric | Before | After (projected) | Delta |
|--------|--------|-------------------|-------|
| Open fixes | 195 | ~140 | about −55 on auto path |
| Auto-safe remaining | 67 | **9** (existing lineage PRs) | −58 |
| Human | 63 | 63 | 0 (needs phone/Settings) |
| Agent | ~65–68 | ~68 | gated agent work not run |
| Mean attention | 25.0 | ~23.7 | small drop |

Attention on **default branches** only falls further after you **merge** the opened Argus PRs. Direct API changes (topics, descriptions, Dependabot/secret alerts) already landed.

## Batched follow-up (after quota reset)

- Waited for core reset → `argus fix --apply --skip-profile` with batching.
- Remaining **9** `LINEAGE-MISSING-MARKERS` applied (existing-PR 422 treated as success / new PRs).
- Projected **auto_safe: 0**. Human 63 / agent ~69 still open (not auto).
- Quota after run: ~3532/5000 remaining (no hard fail).
- Change log: local `dist/APPLY_HISTORY.md` + private [`argus-runner/argus-history/APPLY_HISTORY.md`](https://github.com/edwardlthompson/argus-runner/blob/main/argus-history/APPLY_HISTORY.md).

## YOLO pass (finish cleanup)

- Set `apply_mode: yolo`; implemented auto-merge + handlers in `argus/yolo.py`.
- Open fixes **100 → 10** (−90): icons, Dependabot security updates, What-this-is-not, memory layout, etc.
- Open `chore/argus` PRs after YOLO merge: **0**.
- Still open by design: **PR-STALE** (8), **CI-LATEST-FAILED** (1), plus profile `SEC-CODEQL` 404 when Overview was touched before skip cleared humans.

## What you should do next

1. Optional: triage PR-STALE / red CI manually (not safe to auto-close/merge).
2. Optional: `argus fix --dry-run --skip-profile` for a post-merge scorecard ([`RATE_LIMIT.md`](RATE_LIMIT.md)).
3. History: private [`argus-history/APPLY_HISTORY.md`](https://github.com/edwardlthompson/argus-runner/blob/main/argus-history/APPLY_HISTORY.md).
4. Kill switch if needed: `apply_mode: normal` in `config/safety.yaml`.

## App workflow change

- `--skip-profile` / `--with-profile` on `argus run` and `argus fix`
- Health delta banner in `report.html` + `docs/WEEKLY_APPLY.md`
