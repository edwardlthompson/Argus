# Profile Overview (operator setup)

Argus can open a PR on your public GitHub profile repo (`YOU/YOU`) with a skills portfolio README: hero banner, About, Focus / What I build, featured apps (icons + Stars / Watching / Forks / Views), tech stack, and open-to cards.

Live data comes from the GitHub API. YAML only supplies **your voice** and layout knobs — do not invent achievements.

## First-time setup

1. **Copy the template config** (after a fresh fork or if you want a clean slate):

   ```bash
   cp config/profile_readme.yaml.example config/profile_readme.yaml
   ```

2. **Edit** `config/profile_readme.yaml`:
   - Set `enabled: true`
   - Fill `tagline`, `about`, `principles`, `current_focus`, `open_to_cards`
   - Optional: `featured_repos`, `icon_overrides`, `email`, `argus_repo` (footer link, e.g. `YOU/Argus`)

3. **Icons** — put a square PNG at a canonical path in each product repo (see [`PROFILE_ICONS.md`](PROFILE_ICONS.md)). Hygiene flags `BRAND-ICON-MISSING` when missing. Argus generates a simple PNG mark when none is found.

4. **Token** — `GITHUB_TOKEN` / runner token needs push on `YOU/YOU` and Insights Traffic read on your repos (`repo` scope as needed). Human fix `TRAFFIC-INSIGHTS-UNAVAILABLE` appears when traffic is denied.

5. **Dry-run then apply** (from a clone with deps installed):

   ```bash
   argus doctor
   argus run --dry-run --with-profile --no-notify
   # when ready (often on the private runner / Tuesday weekly):
   argus run --apply --with-profile --no-notify
   # PC fallback when Actions is out:
   argus local-weekly --apply
   ```

6. **Merge** the Overview PR on `YOU/YOU` (`chore/argus-profile-readme`). Keep that repo **public**.

## Weekly refresh (required cadence)

Every Tuesday `argus-weekly` / `local-weekly --apply` refreshes the Overview when `sync_profile: true` (default in `config/safety.yaml`):

| Signal | Behavior |
|--------|----------|
| Stars / forks / watches | Re-fetched from the GitHub API |
| Views | Insights Traffic (~14 days) when the token can read it |
| Icons | Full rescan of canonical paths + overrides; generated marks if still missing |
| Public ↔ private | Visibility re-checked; private/archived drop out of featured; newly public repos can enter |
| Membership | Portfolio discover + Overview eligibility (`_eligible`) drive add/remove |

`yolo.skip_profile: true` still means Argus will not auto_safe/merge hygiene into `YOU/YOU` — only the Overview README PR.

## What gets written to YOU/YOU

| Path | Role |
|------|------|
| `README.md` | Overview body (`<!-- argus:profile-readme -->`) |
| `assets/argus-banner.svg` | Animated hero (self-hosted; you may replace) |
| `assets/argus-divider.svg` | Accent bar under Featured / Tech stack |
| `assets/octicons/*.svg` | Colored Star / Watching / Fork / Views marks |
| `assets/argus-icons/*.png` | Generated marks for repos without icons |

## Ranking and stats

- Featured fill order: **Views + Stars + Watching + Forks** (raw sum). Curated `featured_repos` still lead when set.
- Views = GitHub Insights Traffic (≈14 days). Clones are not shown on the Overview.
- Profile homepage `github.com/YOU` has no public views API; Argus shows Insights views for the **`YOU/YOU` README repo** when `show_profile_views: true`.

## Related config

| File | Purpose |
|------|---------|
| `config/profile_readme.yaml` | Voice + layout (your copy of the example) |
| `config/profile_skills.yaml` | Auto Focus / What I build cards |
| `config/profile_stack.yaml` | Grouped tech stack |
| `config/profile_icons.yaml` | Canonical icon paths + stub rules |
| `config/fixes/profile.yaml` | `PROF-README` auto_safe |
| `config/fixes/portfolio.yaml` | `BRAND-ICON-MISSING`, `TRAFFIC-INSIGHTS-UNAVAILABLE` |

## Hygiene profiles

- Default CLI profile: **`generic`** (safe for any operator).
- `config/profiles/edward.yaml` is a **maintainer-stricter** catalogue for this product’s author — use `--profile edward` only if you intend those extra rules.

## Policy

No remote visitor/snake/stats widgets. Motion and color live in self-hosted SVGs under `assets/`. See [`START_HERE.md`](START_HERE.md) and [`FORKING.md`](FORKING.md).
