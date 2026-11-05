"""Responsiveness: stale issues / PR age heuristics."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from argus.github_client import GitHubClient
from argus.models import RepoRecord


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    issues = client.get(
        f"/repos/{repo.owner}/{repo.name}/issues",
        params={"state": "open", "per_page": 30},
    )
    now = datetime.now(UTC)
    stale = 0
    for issue in issues:
        if "pull_request" in issue:
            continue
        updated = datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00"))
        if (now - updated).days >= 90:
            stale += 1
    return {
        "open_issue_sample": len([i for i in issues if "pull_request" not in i]),
        "stale_issues_90d": stale,
    }
