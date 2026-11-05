"""Featured profile repos: curated flagships, views/stars fill, app-icon URLs."""

from __future__ import annotations

from argus.models import RepoPlan, RepoRecord


def _eligible(repo: RepoRecord) -> bool:
    # Public non-archived, including forks; exclude profile Overview repo.
    return not repo.private and not repo.archived and repo.owner != repo.name


def stars_of(repo: RepoRecord) -> int:
    return int((repo.raw or {}).get("stargazers_count") or 0)


def views_of(repo: RepoRecord) -> int:
    return int((repo.raw or {}).get("argus_traffic_views") or 0)


def traffic_of(repo: RepoRecord) -> int:
    raw = repo.raw or {}
    return int(raw.get("argus_traffic_views") or 0) + int(raw.get("argus_traffic_clones") or 0)


def icon_of(repo: RepoRecord) -> str:
    raw = repo.raw or {}
    if raw.get("argus_icon_url"):
        return str(raw["argus_icon_url"])
    return f"https://opengraph.githubassets.com/argus/{repo.owner}/{repo.name}"


def has_app_icon(repo: RepoRecord) -> bool:
    url = str((repo.raw or {}).get("argus_icon_url") or "")
    return bool(url) and "opengraph.githubassets.com" not in url


def forks_of(repo: RepoRecord) -> int:
    return int((repo.raw or {}).get("forks_count") or 0)


def watches_of(repo: RepoRecord) -> int:
    # GitHub "Watch" UI = subscribers; watchers_count aliases stargazers historically.
    return int((repo.raw or {}).get("subscribers_count") or 0)


def _row(p: RepoPlan) -> dict[str, str]:
    return {
        "name": p.repo.full_name,
        "short": p.repo.name,
        "html_url": p.repo.html_url or f"https://github.com/{p.repo.full_name}",
        "description": (p.repo.description or "")[:120],
        "stars": str(stars_of(p.repo)),
        "forks": str(forks_of(p.repo)),
        "watches": str(watches_of(p.repo)),
        "views": str(views_of(p.repo)),
        "traffic": str(traffic_of(p.repo)),
        "icon_url": icon_of(p.repo),
        "visual": "icon" if has_app_icon(p.repo) else "og",
    }


def select_featured(
    plans: list[RepoPlan],
    limit: int,
    *,
    curated: list[str] | None = None,
) -> list[dict[str, str]]:
    """Curated names first; fill by Insights views then stars. limit<=0 = all eligible."""
    by_full = {p.repo.full_name.lower(): p for p in plans if _eligible(p.repo)}
    by_short = {p.repo.name.lower(): p for p in by_full.values()}
    chosen: list[RepoPlan] = []
    seen: set[str] = set()
    unlimited = limit <= 0
    for key in curated or []:
        k = str(key).strip().lower()
        plan = by_full.get(k) or by_short.get(k.split("/")[-1])
        if plan and plan.repo.full_name not in seen:
            chosen.append(plan)
            seen.add(plan.repo.full_name)
        if not unlimited and len(chosen) >= limit:
            break
    rest = [p for p in by_full.values() if p.repo.full_name not in seen]
    rest.sort(key=lambda p: (-views_of(p.repo), -stars_of(p.repo), p.repo.name.lower()))
    for p in rest:
        if not unlimited and len(chosen) >= limit:
            break
        chosen.append(p)
    return [_row(p) for p in chosen]


def profile_repo_views(plans: list[RepoPlan], login: str) -> int | None:
    """14-day Insights views for YOU/YOU when present in plans."""
    if not login:
        return None
    key = f"{login}/{login}".lower()
    for plan in plans:
        if plan.repo.full_name.lower() == key:
            return views_of(plan.repo)
    return None


def center_grid_rows(
    items: list[dict[str, str]], columns: int
) -> list[list[dict[str, str] | None]]:
    """Chunk into rows; pad short rows with None so cells stay center-justified."""
    cols = max(1, columns)
    rows: list[list[dict[str, str] | None]] = []
    for i in range(0, len(items), cols):
        chunk: list[dict[str, str] | None] = list(items[i : i + cols])
        if len(chunk) < cols:
            left = (cols - len(chunk)) // 2
            right = cols - len(chunk) - left
            chunk = [None] * left + chunk + [None] * right
        rows.append(chunk)
    return rows


def apply_icon_overrides(plans: list[RepoPlan], overrides: dict[str, str] | None) -> None:
    """YAML icon_overrides: short name or full_name -> https URL."""
    if not overrides:
        return
    norm = {str(k).strip().lower(): str(v).strip() for k, v in overrides.items() if v}
    for plan in plans:
        repo = plan.repo
        url = norm.get(repo.full_name.lower()) or norm.get(repo.name.lower())
        if url:
            raw = dict(repo.raw or {})
            raw["argus_icon_url"] = url
            repo.raw = raw
