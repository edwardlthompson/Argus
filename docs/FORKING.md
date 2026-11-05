# Forking Argus for your own account

1. Click **Fork** on GitHub (or clone and push to your account).
2. In your fork: **Settings → Secrets and variables → Actions**, add `GITHUB_TOKEN` or rely on `secrets.GITHUB_TOKEN` with appropriate permissions.
3. Leave `config/profiles/generic.yaml` as the default profile.
4. Clear or edit `config/status.yaml` for your repos (empty is fine — discovery assigns `active`).
5. Optionally edit `config/allowlist.yaml` if you collaborate on many orgs.
6. Run locally:

```bash
pip install -e ".[dev]"
export GITHUB_TOKEN=…   # or set in .env
argus doctor
argus run --dry-run
```

You should see `dist/runbook.md` and `dist/report.html` for **your** repositories.

No Python changes required for a normal fork.
