# Publish Argus (controller) to GitHub

`[HUMAN]` step — create the remote and push so weekly Actions can scan your portfolio **including Argus itself**.

```bash
# from the Argus project root
gh repo create edwardlthompson/Argus --public --source=. --remote=origin --push
# Stronger: --private  (recommended so Issues + artifacts stay off the open web)
```

Then:

1. **Settings → Actions → General** — allow workflows.
2. **Settings → Pages → Source → GitHub Actions** (optional public **status-only** page).
3. Add secrets if needed: `ARGUS_DISCORD_WEBHOOK` (etc.), optional fine-grained `ARGUS_GITHUB_TOKEN` with repo + issues scope for cross-repo apply and inbox sync.
4. Set variable `ARGUS_REPORT_URL` to the Pages **status** URL after first Pages deploy (counts only).
5. Run **argus-scan** or **argus-weekly** once; download the private artifact for the full report; confirm Issues labeled `argus-inbox` for non-security human tasks when `--apply` is used.

Allow-list stays `owner_only` — no special skip for the controller.

If the repo is public, keep `config/inbox.yaml` → `security_issues: false` (default). Flip to `true` only after the controller is private.
