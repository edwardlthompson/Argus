# Private runner — workflows and token scopes

The **private** runner (`YOU/argus-runner`) owns scheduled scans and apply. The public product repo stays source + CI only.

## Workflows

| Workflow | Trigger | Default |
|----------|---------|---------|
| `argus-weekly` | Monday cron + `workflow_dispatch` | Prefer apply when `apply_mode: yolo` |
| `argus-scan` | `workflow_dispatch` | Choose `apply` / `notify` inputs |
| `ci` | push/PR | tests only |
| `pages` | after weekly/scan success | status-only if enabled |

### Apply input

- Explicit `--dry-run` / `apply=false` — discover, score, artifacts only (no writes).
- Apply / YOLO default — when `config/safety.yaml` has `apply_mode: yolo`, omitting the dry-run flag **implies apply** (`docs/YOLO.md`).
- `apply=true` / `--apply` — always mutative when token allows.

First week on a new runner: run once with `--dry-run`, inspect artifacts, then leave YOLO to apply on the schedule.

### YOLO

Set `apply_mode: yolo` on the private runner (shipped default). Loop: apply → handlers → merge chore/Dependabot patch → optional second pass → private **yolo-digest** Issue for judgment leftovers. Profile Overview stays sacred via `yolo.skip_profile: true`. Grok digests never merge. Full policy: [YOLO.md](YOLO.md) · [GROK_BOTS.md](GROK_BOTS.md).

### Shareable reports

Every run writes:

- `dist/report.html` — dark portfolio HTML
- `dist/portfolio-report.md` — matching Markdown
- `dist/runbook.md` — gated agent paste surface

On the private controller, dated copies sync to `argus-history/reports/YYYY-MM-DD.html` (+ `.md`). Public product Pages stay **status-only** (no per-repo security gaps).

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
