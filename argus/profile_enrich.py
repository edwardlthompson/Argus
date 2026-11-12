"""Enrich RepoPlans for Overview: stars/forks/watches, traffic, icons, languages."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoPlan
from argus.profile_featured import _eligible
from argus.profile_icon_gen import generate_icon_png, icon_asset_path, icon_raw_url
from argus.profile_icons import resolve_icon


def _fill_traffic(client: GitHubClient, repo: object, raw: dict[str, Any]) -> None:
    try:
        views = client.get(f"/repos/{repo.owner}/{repo.name}/traffic/views")
        raw["argus_traffic_views"] = int((views or {}).get("count") or 0)
        raw["argus_traffic_ok"] = True
    except GitHubError:
        raw.setdefault("argus_traffic_views", 0)
        raw["argus_traffic_ok"] = False
    try:
        clones = client.get(f"/repos/{repo.owner}/{repo.name}/traffic/clones")
        raw["argus_traffic_clones"] = int((clones or {}).get("count") or 0)
    except GitHubError:
        raw.setdefault("argus_traffic_clones", 0)


def enrich_plans_for_profile(
    client: GitHubClient,
    plans: list[RepoPlan],
    *,
    profile_login: str | None = None,
) -> dict[str, int]:
    """Fill stargazers/forks/watches, traffic, icons, language bytes."""
    from argus.profile_stack import collect_language_bytes

    login = profile_login or ""
    for plan in plans:
        repo = plan.repo
        host = login or repo.owner
        raw: dict[str, Any] = dict(repo.raw or {})
        # Always refresh visibility + counters so public↔private membership updates weekly.
        try:
            meta = client.get_repo(repo.owner, repo.name)
            repo.private = bool(meta.get("private"))
            repo.archived = bool(meta.get("archived"))
            raw["private"] = repo.private
            raw["archived"] = repo.archived
            raw["stargazers_count"] = int(meta.get("stargazers_count") or 0)
            raw["forks_count"] = int(meta.get("forks_count") or 0)
            raw["subscribers_count"] = int(meta.get("subscribers_count") or 0)
            if meta.get("description"):
                repo.description = str(meta.get("description") or "")
            if meta.get("default_branch"):
                repo.default_branch = str(meta["default_branch"])
            if meta.get("html_url"):
                repo.html_url = str(meta["html_url"])
        except GitHubError:
            raw.setdefault("stargazers_count", 0)
            raw.setdefault("forks_count", 0)
            raw.setdefault("subscribers_count", 0)
        repo.raw = raw
        if repo.private or repo.archived:
            # Drop stale Overview fields when a repo goes private/archived.
            raw.pop("argus_icon_url", None)
            raw.pop("argus_icon_png", None)
            raw.pop("argus_traffic_views", None)
            continue
        is_profile = repo.owner == repo.name
        if not is_profile and not _eligible(repo):
            continue
        _fill_traffic(client, repo, raw)
        repo.raw = raw
        if is_profile:
            continue
        # Full icon rescan every Overview sync (new marks, removals, overrides).
        icon = resolve_icon(client, repo)
        raw = dict(repo.raw or {})
        raw.pop("argus_icon_png", None)
        raw.pop("argus_icon_path", None)
        if icon:
            raw["argus_icon_url"] = icon
        else:
            png = generate_icon_png(repo.name, repo.description)
            raw["argus_icon_png"] = png
            raw["argus_icon_path"] = icon_asset_path(repo.name)
            raw["argus_icon_url"] = icon_raw_url(host, repo.name)
        repo.raw = raw
    return collect_language_bytes(client, plans)


def collect_generated_icons(plans: list[RepoPlan]) -> dict[str, bytes]:
    """Path → PNG bytes for Overview PR upload."""
    out: dict[str, bytes] = {}
    for plan in plans:
        raw = plan.repo.raw or {}
        path = raw.get("argus_icon_path")
        png = raw.get("argus_icon_png")
        if isinstance(path, str) and isinstance(png, (bytes, bytearray)):
            out[path] = bytes(png)
    return out
