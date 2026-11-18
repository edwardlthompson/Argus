"""GitHub Insights Traffic (14-day views/clones) — owner/push required."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    """Probe Insights Traffic; traffic_ok False when API denies or errors."""
    if not repo.can_write:
        return {"traffic_ok": False, "views_14d": None, "clones_14d": None, "skipped": True}
    views_n: int | None = None
    clones_n: int | None = None
    ok = True
    try:
        views = client.get(f"/repos/{repo.owner}/{repo.name}/traffic/views")
        views_n = int((views or {}).get("count") or 0)
    except GitHubError:
        ok = False
    try:
        clones = client.get(f"/repos/{repo.owner}/{repo.name}/traffic/clones")
        clones_n = int((clones or {}).get("count") or 0)
    except GitHubError:
        ok = False
    return {
        "traffic_ok": ok,
        "views_14d": views_n,
        "clones_14d": clones_n,
        "skipped": False,
    }
