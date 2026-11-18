# Release freshness (local CLI)

Argus can scan Edward’s portfolio for missing or stale GitHub Releases and open a **release-prep PR** in each flagged repo. It **never** runs from GitHub Actions (that would spend the same minutes this check is trying to protect). It **never** cuts tags, publishes releases, force-pushes, or merges.

Use a machine with a `GITHUB_TOKEN` (his PC, or a Linux box crontab). REST only.

## Commands

```bash
# Default = dry-run (no PRs)
argus releases --dry-run
# or just:
argus releases

# Scan one user. If the token IS that user, private repos are included
# (needed to see billed Actions minutes). `/users/{user}/repos` is public-only.
argus releases --dry-run --owner edwardlthompson
argus releases --dry-run --owner edwardlthompson --public-only

# One repo
argus releases --dry-run --repo edwardlthompson/Google-Messages-For-Desktop

# Live PRs (write token). Still never tags or publishes.
argus releases --open-prs
argus releases --open-prs --max-prs 5
```

Artifacts: `dist/releases-report.md` and `dist/releases-report.html` (private — not Pages).

The report has:

1. **Grandma list** — repo, platforms, last release/date, what’s missing, PR link.
2. **Actions minutes** — existing workflows that run on **every push**, **pull_request**, or **schedule**, plus visibility (public standard minutes are free; private minutes bill; macOS is ~10×). Argus does **not** edit those workflows.

## Enable live PRs

1. Token scopes: classic `repo` (or fine-grained **Contents: read/write** + **Pull requests: write** on the target repos). Read is enough for dry-run.
2. Keep `config/releases.yaml` `open_prs: false` (documented default). Pass **`--open-prs`** when you intend to write.
3. Optional: `--notify` sends the grandma list to Discord/Telegram/webhook if those env secrets are set.

## What a release-prep PR does

- Adds a **new** tag-triggered workflow (does not rewrite existing CI): `on.push.tags: v*` and `workflow_dispatch` only. No matrix on branch pushes.
- Builds/attaches unsigned artifacts per inferred platform (Android APK, Electron/Tauri desktop, Python wheels, PWA zip). Private repos **omit `macos-latest`** (note in the PR body).
- Bumps the next patch (or `bump: minor` in YAML) and updates CHANGELOG.
- PR body contains the exact tag command for Edward:

```bash
git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z
```

If the repo is too irregular (iOS signing, a release workflow that already runs on every push), Argus **does not guess**. The repo is listed as irregular and the `RELEASE-IRREGULAR` gated agent prompt is in `config/fixes/releases.yaml`.

Duplicate Argus release-prep PRs/branches are updated or skipped.

## Crontab (Linux)

Export `GITHUB_TOKEN` (or `ARGUS_GITHUB_TOKEN`) in the crontab environment, or source `.env`:

```cron
# Tuesday 09:00 local — REST only, not Actions
0 9 * * 2 cd /home/edward/Argus && set -a && . ./.env && set +a && . .venv/bin/activate && argus releases --dry-run --owner edwardlthompson
```

Live PRs (after you trust dry-runs):

```cron
0 9 * * 2 cd /home/edward/Argus && set -a && . ./.env && set +a && . .venv/bin/activate && argus releases --open-prs --max-prs 5
```

Wrapper: `scripts/local-releases.sh`.

## Windows Task Scheduler

```powershell
# From an elevated or user PowerShell, weekly Tuesday 09:00
schtasks /Create /TN ArgusReleases /SC WEEKLY /D TUE /ST 09:00 `
  /TR "pwsh -NoProfile -File C:\Users\edwar\Argus\scripts\local-releases.ps1"
```

`scripts/local-releases.ps1` defaults to `--dry-run`. Pass `-OpenPrs` when you want PRs. Set `GITHUB_TOKEN` (classic `repo` scope) in the user environment so Task Scheduler can list **private** repos — those are the ones that bill Actions minutes.

## Config

`config/releases.yaml` — stale window (90 days), skip lists (archived, parked, forks, docs-only, profile repos, deny/allow), platforms, `macos_runners: public_only`.

Do **not** add this command to `.github/workflows/weekly.yml` or any Argus Actions workflow.
