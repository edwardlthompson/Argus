"""Momentum signals: push/activity freshness."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from argus.github_client import GitHubClient
from argus.models import RepoRecord


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    raw = repo.raw or client.get_repo(repo.owner, repo.name)
    pushed = raw.get("pushed_at")
    days = None
    if pushed:
        dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        days = max(0, (datetime.now(UTC) - dt).days)
    return {
        "days_since_push": days,
        "open_issues": int(raw.get("open_issues_count") or 0),
        "stargazers": int(raw.get("stargazers_count") or 0),
        "fork": bool(raw.get("fork")),
    }
