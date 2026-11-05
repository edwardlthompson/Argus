# Publish Argus (public product)

Create the **public** MIT product remote (source + CI + docs). Real portfolio scans run on a **private runner** — see [FORKING.md](FORKING.md).

```bash
gh repo create YOUR_LOGIN/Argus --public --source=. --remote=origin --push
```

Then on the **public** product:

1. **Settings → Actions** — allow workflows (CI / Pages status-only).
2. Optional **Pages** → GitHub Actions for **status counts only** (`status.html`).
3. Do **not** put your portfolio PAT apply secrets here if the repo is public and you sync Issues with security detail.
4. Set `ARGUS_REPORT_URL` only to a **status-only** Pages URL if used in digests.

## Private runner (required for auto scan / auto-fix)

```bash
pwsh -File scripts/bootstrap-argus-runner.ps1
# or: bash scripts/bootstrap-argus-runner.sh
```

On the private runner:

| Secret / input | Purpose |
|----------------|---------|
| `ARGUS_GITHUB_TOKEN` | Fine-grained or classic PAT: read portfolio + write PRs/issues as needed |
| Discord/Telegram secrets | Optional digests |
| Workflow `apply=true` | Enable `auto_safe` + Issues sync |

Public product CI should stay tests/fixtures — not a live apply against the world.
