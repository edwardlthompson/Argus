# Publish Argus (controller) to GitHub

`[HUMAN]` step — create the remote and push so weekly Actions can scan your portfolio **including Argus itself**.

```bash
# from the Argus project root
gh repo create edwardlthompson/Argus --public --source=. --remote=origin --push
```

Then:

1. **Settings → Actions → General** — allow workflows.
2. **Settings → Pages → Source → GitHub Actions**.
3. Add secrets if needed: `ARGUS_DISCORD_WEBHOOK` (etc.), optional fine-grained `ARGUS_GITHUB_TOKEN` with repo scope for cross-repo apply.
4. Set variable `ARGUS_REPORT_URL` to the Pages URL after first Pages deploy.
5. Run **argus-weekly** once; confirm `edwardlthompson/Argus` appears in `dist/report.html`.

Allow-list stays `owner_only` — no special skip for the controller.
