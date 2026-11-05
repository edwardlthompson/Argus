"""Open / stale pull request signals."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    try:
        pulls = client.get(
            f"/repos/{repo.owner}/{repo.name}/pulls",
            params={"state": "open", "per_page": 30},
        )
    except GitHubError:
        return {"open_prs": 0, "stale_prs_30d": 0, "failed_check_prs": 0}

    now = datetime.now(UTC)
    stale = 0
    for pr in pulls:
        updated = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
        if (now - updated).days >= 30:
            stale += 1
    return {
        "open_prs": len(pulls),
        "stale_prs_30d": stale,
        "draft_prs": sum(1 for p in pulls if p.get("draft")),
    }
