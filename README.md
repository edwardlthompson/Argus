# Argus

**One controller to rule them all** — autonomous multi-repo hygiene, scoring, safe auto-apply, gated agentic execution, and grandma-simple human notifications.

Argus runs mostly silently. When a human is truly needed, you get a clear HTML report and a short notification — not a wall of jargon.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env   # set GITHUB_TOKEN
argus doctor
argus run --dry-run
```

Open `dist/report.html`.

Scan someone else’s public repos (read-only):

```bash
argus report --target some-user --public-only
```

## What you get

- Dynamic discovery of new, removed, parked, and archived repositories
- Opinionated hygiene constitution in `config/fixes.yaml` (data, not hard-coded Python)
- Auto-apply **only** for deterministic `auto_safe` fixes (PRs preferred, dry-run default)
- One gated agent prompt per repo (≤4 phases, every phase ends with `GATE:`)
- Notifications only when human work remains or critical security signals appear

## What Argus is not

- Not a coding agent that lives inside every product repository
- Not a replacement for Dependabot/Renovate (it complements them)
- Not allowed to force-push, rewrite history, or delete repositories
- Not silent about unexpected failures

## Docs

- [START_HERE.md](docs/START_HERE.md)
- [PROFILE_OVERVIEW.md](docs/PROFILE_OVERVIEW.md) — public GitHub profile README portfolio
- [PROFILE_ICONS.md](docs/PROFILE_ICONS.md) — canonical app icons + hygiene
- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [SAFETY.md](docs/SAFETY.md)
- [GRANDMA_MODE.md](docs/GRANDMA_MODE.md)
- [FORKING.md](docs/FORKING.md)
- [THIRD_PARTY.md](docs/THIRD_PARTY.md)

## Parent template

Argus is a **product child** of [`edwardlthompson/agent-project-bootstrap`](https://github.com/edwardlthompson/agent-project-bootstrap) (pinned in `.template-version`). Gap list: [`docs/PARENT_GAP_LIST.md`](docs/PARENT_GAP_LIST.md). Upgrades: [`docs/UPGRADING_FROM_TEMPLATE.md`](docs/UPGRADING_FROM_TEMPLATE.md).

## License

MIT

## What this is not

- A finished commercial product promise
- A place for secrets or production credentials
- An unbounded scope — see README goals above

