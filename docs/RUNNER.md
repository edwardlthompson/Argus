# Private runner — workflows and token scopes

The **private** runner (`YOU/argus-runner`) owns scheduled scans and apply. The public product repo stays source + CI only.

## Workflows

| Workflow | Trigger | Default |
|----------|---------|---------|
| `argus-weekly` | Monday cron + `workflow_dispatch` | `apply=false` (dry-run) |
| `argus-scan` | `workflow_dispatch` | Choose `apply` / `notify` inputs |
| `ci` | push/PR | tests only |
| `pages` | after weekly/scan success | status-only if enabled |

### Apply input

- `apply=false` — discover, score, artifacts, dry-run inbox/profile sync (no writes).
- `apply=true` — `auto_safe` PRs, Issues inbox writes, profile README PR when due.

First week: leave apply false. Inspect the artifact. Then run **argus-scan** with `apply=true`.

## Secrets (runner only)

| Name | Scope needed | Purpose |
|------|----------------|---------|
| `ARGUS_GITHUB_TOKEN` | Fine-grained: Contents R/W on targets you own, Issues R/W on runner, Metadata | Cross-repo apply + inbox + profile PR |
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
  -f client_payload='{"apply":"false","notify":"true"}'
```

Wire Discord/Telegram bots to that API with a server-side secret — never put the PAT in the chat client.

## Bootstrap

```bash
pwsh -File scripts/bootstrap-argus-runner.ps1
# or: bash scripts/bootstrap-argus-runner.sh
```

See [FORKING.md](FORKING.md) · [WEEKLY_APPLY.md](WEEKLY_APPLY.md) · [THREAT_MODEL.md](THREAT_MODEL.md).
