# Forking Argus (public product + private runner)

Argus is a **public MIT product**. Real scans, auto-apply, Issues inbox, and artifacts belong on a **private runner** so findings stay owner-only.

## Recommended path (operators)

1. Use / fork / clone the **public** `Argus` repo for source and contributions.
2. Bootstrap a private runner (one command):

```bash
# from a clone of public Argus, with gh authenticated (repo + workflow scopes)
pwsh -File scripts/bootstrap-argus-runner.ps1
# or: bash scripts/bootstrap-argus-runner.sh
```

That creates `YOU/argus-runner` (private), pushes code, sets `ARGUS_GITHUB_TOKEN`, points `config/inbox.yaml` at the runner with `security_issues: true`, and queues a dry-run scan.

3. Watch Actions on the **private** runner. When the dry-run looks sane, re-run **argus-scan** with `apply=true` (or weekly input).
4. Live in: private Issues (`argus-inbox`) + Actions artifacts + optional Discord/Telegram digests.

## Local dry-run (optional)

```bash
pip install -e ".[dev]"
cp .env.example .env   # set GITHUB_TOKEN
argus doctor
argus run --dry-run
```

Open `dist/report.html` locally. Do **not** point a public product repo’s inbox at your real findings.

## Contributing

Open PRs against the **public** product. Do not commit secrets or real portfolio dumps.

## Profile Overview

Full checklist: [`docs/PROFILE_OVERVIEW.md`](PROFILE_OVERVIEW.md).

```bash
cp config/profile_readme.yaml.example config/profile_readme.yaml
# edit voice, set enabled: true, optional argus_repo: YOU/Argus
```

Argus PRs an updated README into public `YOU/YOU` (banner, divider, octicons, featured grid). Keep that repo **public**.

Retune in YAML (not Python):

- `config/profile_readme.yaml` — voice, `featured_repos`, `current_focus`, `open_to_cards`, `icon_overrides`, `argus_repo`, optional `email`
- `config/profile_skills.yaml` — auto Focus / What I build when roles/capabilities are empty
- `config/profile_stack.yaml` — grouped tech stack from languages + topics
- `config/profile_icons.yaml` — canonical app-icon paths (hygiene `BRAND-ICON-MISSING`)

Hand-crafted banner: commit your own `assets/argus-banner.svg` in `YOU/YOU` (self-hosted SVG only; avoid third-party stats widgets).

Default hygiene profile is **`generic`**. `config/profiles/edward.yaml` is maintainer-stricter for this product’s author — only use `--profile edward` if you want those extra rules.
