# Publish Argus (public product)

Create the **public** MIT product remote (source + CI + docs). Real portfolio scans run on a **private runner** — see [FORKING.md](FORKING.md).

```bash
gh repo create YOUR_LOGIN/Argus --public --source=. --remote=origin --push
```

Then on the **public** product:

1. **Settings → Actions** — allow workflows (CI / Pages).
2. Optional **Pages** → GitHub Actions for the **sanitized** portfolio dashboard (`portfolio-pages.html` → metrics/graphs only). GitHub Pages URLs are public and scrapable.
3. Full weakness reports stay on the **private runner** under `argus-history/reports/latest.html` (login + repo access). Never publish `report.html` / `steward-brief.html` to Pages.
4. Do **not** put your portfolio PAT apply secrets on the public product if Issues sync security detail.
5. Set `ARGUS_REPORT_URL` only to the **sanitized** Pages URL if used in digests / Steward webhook.

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
