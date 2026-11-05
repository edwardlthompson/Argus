"""Release / shipping signals."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    try:
        releases = client.get(
            f"/repos/{repo.owner}/{repo.name}/releases",
            params={"per_page": 5},
        )
        count = len(releases) if isinstance(releases, list) else 0
        latest = releases[0]["tag_name"] if count else None
    except GitHubError:
        count = 0
        latest = None
    return {
        "release_count": count,
        "latest_tag": latest,
        "has_release": count > 0,
    }
