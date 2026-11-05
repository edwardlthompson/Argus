"""Featured profile repos: stars + traffic ranking and app-icon URLs."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoPlan, RepoRecord

# Common launcher / brand asset paths (checked in order).
_ICON_PATHS = (
    "icon.png",
    "icon.svg",
    "logo.png",
    "logo.svg",
    "app-icon.png",
    "app_icon.png",
    "brand.png",
    "assets/icon.png",
    "assets/logo.png",
    "assets/logo.svg",
    "assets/brand.png",
    "docs/icon.png",
    "docs/logo.png",
    "images/icon.png",
    "img/icon.png",
    "media/icon.png",
    "branding/icon.png",
    "res/icon.png",
    "fastlane/metadata/android/en-US/images/icon.png",
    "metadata/en-US/images/icon.png",
    "app/ic_launcher-playstore.png",
    "android/app/src/main/ic_launcher-playstore.png",
    "src/main/ic_launcher-playstore.png",
    "composeApp/ic_launcher-playstore.png",
)


def _eligible(repo: RepoRecord) -> bool:
    return (
        not repo.private
        and not repo.archived
        and not repo.fork
        and repo.owner != repo.name
    )


def stars_of(repo: RepoRecord) -> int:
    return int((repo.raw or {}).get("stargazers_count") or 0)


def traffic_of(repo: RepoRecord) -> int:
    raw = repo.raw or {}
    return int(raw.get("argus_traffic_views") or 0) + int(raw.get("argus_traffic_clones") or 0)


def icon_of(repo: RepoRecord) -> str:
    raw = repo.raw or {}
    if raw.get("argus_icon_url"):
        return str(raw["argus_icon_url"])
    # Stable fallback: GitHub Open Graph card image for the repo.
    return f"https://opengraph.githubassets.com/argus/{repo.owner}/{repo.name}"


def has_app_icon(repo: RepoRecord) -> bool:
    """True when we resolved a repo asset (not OG placeholder)."""
    url = str((repo.raw or {}).get("argus_icon_url") or "")
    return bool(url) and "opengraph.githubassets.com" not in url


def select_featured(plans: list[RepoPlan], limit: int) -> list[dict[str, str]]:
    """Rank public non-fork apps by stars, then traffic (views+clones)."""
    cands = [p for p in plans if _eligible(p.repo)]
    cands.sort(
        key=lambda p: (
            -stars_of(p.repo),
            -traffic_of(p.repo),
            p.repo.name.lower(),
        )
    )
    out: list[dict[str, str]] = []
    for p in cands[:limit]:
        app_icon = has_app_icon(p.repo)
        out.append(
            {
                "name": p.repo.full_name,
                "short": p.repo.name,
                "html_url": p.repo.html_url or f"https://github.com/{p.repo.full_name}",
                "description": (p.repo.description or "")[:120],
                "stars": str(stars_of(p.repo)),
                "traffic": str(traffic_of(p.repo)),
                "icon_url": icon_of(p.repo),
                "visual": "icon" if app_icon else "og",
            }
        )
    return out


def _resolve_icon(client: GitHubClient, repo: RepoRecord) -> str | None:
    for path in _ICON_PATHS:
        try:
            data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        except GitHubError:
            continue
        if isinstance(data, dict) and data.get("download_url"):
            return str(data["download_url"])
        if isinstance(data, list):
            continue
    return None


def enrich_plans_for_profile(client: GitHubClient, plans: list[RepoPlan]) -> dict[str, int]:
    """Fill stargazers, traffic, icons, and language bytes. Returns language totals."""
    from argus.profile_stack import collect_language_bytes

    for plan in plans:
        repo = plan.repo
        if not _eligible(repo):
            continue
        raw: dict[str, Any] = dict(repo.raw or {})
        if "stargazers_count" not in raw:
            try:
                meta = client.get_repo(repo.owner, repo.name)
                raw["stargazers_count"] = int(meta.get("stargazers_count") or 0)
                if meta.get("description") and not repo.description:
                    repo.description = meta.get("description")
                if meta.get("default_branch"):
                    repo.default_branch = str(meta["default_branch"])
            except GitHubError:
                raw.setdefault("stargazers_count", 0)
        try:
            views = client.get(f"/repos/{repo.owner}/{repo.name}/traffic/views")
            raw["argus_traffic_views"] = int((views or {}).get("count") or 0)
        except GitHubError:
            raw.setdefault("argus_traffic_views", 0)
        try:
            clones = client.get(f"/repos/{repo.owner}/{repo.name}/traffic/clones")
            raw["argus_traffic_clones"] = int((clones or {}).get("count") or 0)
        except GitHubError:
            raw.setdefault("argus_traffic_clones", 0)
        icon = _resolve_icon(client, repo)
        if icon:
            raw["argus_icon_url"] = icon
        else:
            raw["argus_icon_url"] = (
                f"https://opengraph.githubassets.com/argus/{repo.owner}/{repo.name}"
            )
        repo.raw = raw
    return collect_language_bytes(client, plans)
