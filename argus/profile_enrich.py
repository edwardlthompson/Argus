"""Enrich RepoPlans for Overview: stars/forks/watches, traffic, icons, languages."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoPlan
from argus.profile_featured import _eligible, has_app_icon
from argus.profile_icons import resolve_icon


def enrich_plans_for_profile(client: GitHubClient, plans: list[RepoPlan]) -> dict[str, int]:
    """Fill stargazers/forks/watches, traffic, icons, language bytes."""
    from argus.profile_stack import collect_language_bytes

    for plan in plans:
        repo = plan.repo
        if not _eligible(repo):
            continue
        raw: dict[str, Any] = dict(repo.raw or {})
        try:
            meta = client.get_repo(repo.owner, repo.name)
            raw["stargazers_count"] = int(meta.get("stargazers_count") or 0)
            raw["forks_count"] = int(meta.get("forks_count") or 0)
            raw["subscribers_count"] = int(meta.get("subscribers_count") or 0)
            if meta.get("description") and not repo.description:
                repo.description = meta.get("description")
            if meta.get("default_branch"):
                repo.default_branch = str(meta["default_branch"])
        except GitHubError:
            raw.setdefault("stargazers_count", 0)
            raw.setdefault("forks_count", 0)
            raw.setdefault("subscribers_count", 0)
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
        repo.raw = raw
        if not has_app_icon(repo):
            icon = resolve_icon(client, repo)
            raw = dict(repo.raw or {})
            raw["argus_icon_url"] = icon or (
                f"https://opengraph.githubassets.com/argus/{repo.owner}/{repo.name}"
            )
            repo.raw = raw
    return collect_language_bytes(client, plans)
