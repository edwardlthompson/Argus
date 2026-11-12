# Private runner — workflows and token scopes

The **private** runner (`YOU/argus-runner`) owns scheduled scans and apply. The public product repo stays source + CI only.

## Workflows

| Workflow | Trigger | Default |
|----------|---------|---------|
| `argus-weekly` | **Tuesday** cron (14:00 UTC, after Monday Dependabot) + `workflow_dispatch` on **private `argus-runner` only** | Prefer apply when YOLO armed (`yolo.on` / `apply_mode: yolo`); fix+soft-merge upgrades. Public product `weekly.yml` is **`workflow_dispatch` only** (no cron) — never schedule YOLO on public Argus. |
| `argus-scan` | `workflow_dispatch` | Choose `apply` / `notify` inputs |
| `ci` | push/PR | tests only |
| `pages` | after weekly/scan success | status-only if enabled |

### Apply input

- Explicit `--dry-run` / `apply=false` — discover, score, artifacts only (no writes).
- Apply / YOLO default — when the runner is YOLO-armed (`yolo.on` or `apply_mode: yolo`), omitting the dry-run flag **implies apply** (`docs/YOLO.md`).
- `apply=true` / `--apply` — always mutative when token allows.

First week on a new runner: run once with `--dry-run`, inspect artifacts, then leave YOLO to apply on the schedule.

### YOLO

Bootstrap writes `yolo.on` and sets runner `apply_mode: yolo` (public product template stays `normal`). Loop: apply → handlers → fix/heal upgrade PRs → six pre-merge checks → squash chore/upgrade (incl. soft-allowlist noise) / Dependabot patch → action ledger → optional second pass → private **yolo-digest** Issue for judgment leftovers only (no per-finding creator pings). **Tuesday Overview refresh:** `yolo.sync_profile: true` opens/updates the public `YOU/YOU` README PR with live stars/forks/views, icon rescan, and public↔private membership (`skip_profile` only blocks auto_safe into `YOU/YOU`). Weekly workflow passes `--with-profile`; `local-weekly` does the same when Actions is out. **Grok never merges** — optional **Tuesday Steward** digests leftovers after the Tuesday run. Kill: delete `yolo.on` or add `YOLO-OFF.md`. Full policy: [YOLO.md](YOLO.md) · [GROK_BOTS.md](GROK_BOTS.md).

Sync this product’s `weekly.yml` **job body** (and Tuesday cron) to the private `argus-runner` when upgrading the runner clone. Cron must remain on the runner only; the public product workflow stays dispatch-only.

### Shareable reports

Every run writes:

- `dist/report.html` — full dark portfolio HTML (private; finding titles included)
- `dist/portfolio-report.md` — matching Markdown
- `dist/steward-brief.html` — Tuesday Steward visual (private; never Pages)
- `dist/portfolio-pages.html` — sanitized public dashboard (metrics/graphs only)
- `dist/runbook.md` — gated agent paste surface

On the private controller, sync to `argus-history/reports/`:

- dated `YYYY-MM-DD.html|.md` plus `*-steward.html` / `*-infographic.svg`
- `latest.html`, `latest.md`, `latest-steward.html`, `latest-infographic.svg`

**Pages are world-readable.** Public product Pages deploy only `portfolio-pages.html` (or legacy status). Never stage `report.html`, `runbook.md`, `inbox.json`, or `steward-brief.html`.

### Apply history

Append-only `argus-history/` on the private runner (see [RATE_LIMIT.md](RATE_LIMIT.md)).

## Secrets (runner only)

| Name | Scope needed | Purpose |
|------|----------------|---------|
| `ARGUS_GITHUB_TOKEN` | Fine-grained: Contents R/W on targets you own, Issues R/W on runner, Metadata | Cross-repo apply + inbox + digest + history |
| `ARGUS_DISCORD_WEBHOOK` | — | Optional digest |
| `ARGUS_TELEGRAM_BOT_TOKEN` + `ARGUS_TELEGRAM_CHAT_ID` | — | Optional digest |
| `ARGUS_WEBHOOK_URL` | — | Optional generic webhook |

`GITHUB_TOKEN` from Actions is enough for CI and uploading artifacts on the runner itself; prefer `ARGUS_GITHUB_TOKEN` for portfolio writes.

## Actions-out fallback (free tier / no payment card)

Argus must keep working when GitHub Actions minutes are exhausted or the account has **no paid plan / no card**. **Do not** treat “add billing” as the fix.

When Actions cannot start jobs, **argus-weekly on the runner will not run**. Use This Computer (free):

```powershell
# PowerShell — token already in env (same PAT as ARGUS_GITHUB_TOKEN)
pwsh -File scripts/local-weekly.ps1
# dry-run only:
pwsh -File scripts/local-weekly.ps1 -DryRun
```

```bash
bash scripts/local-weekly.sh
# or: python -m argus local-weekly --apply
# force free-tier merge path: argus merge-upgrades --allow-unarmed --actions-unavailable --fix
```

Defaults (`yolo.skip_ci_when_actions_unavailable`, `merge_when_actions_billing`): upgrade merges skip remote CI when Actions is unavailable (auto-detect zero-step failures, billing annotations, or `ARGUS_ACTIONS_UNAVAILABLE=1`). Ledger notes `actions_unavailable`. Paying for Actions is optional, never required.

## Projects board (optional)

Create a GitHub Project (v2) on the private runner owner. In runner `config/inbox.yaml`:

```yaml
project_owner: YOUR_LOGIN   # user or org that owns the project
project_number: 1           # from the project URL
```

Open `argus-inbox` Issues are added to the board after each scan (dry-run lists would-add only).

## Chat → scan (`repository_dispatch`)

From a trusted automation (server with a PAT that can dispatch on the **private** runner):

```bash
gh api repos/YOU/argus-runner/dispatches \
  -f event_type=argus-scan \
  -f client_payload='{"apply":"true","notify":"true"}'
```

Wire Discord/Telegram bots to that API with a server-side secret — never put the PAT in the chat client.

## Bootstrap

```bash
pwsh -File scripts/bootstrap-argus-runner.ps1
# or: bash scripts/bootstrap-argus-runner.sh
```

See [FORKING.md](FORKING.md) · [WEEKLY_APPLY.md](WEEKLY_APPLY.md) · [THREAT_MODEL.md](THREAT_MODEL.md).
