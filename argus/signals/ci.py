"""CI presence and recent run health on default branch."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    has_workflows = False
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/actions/workflows")
        has_workflows = int(data.get("total_count") or 0) > 0
    except GitHubError:
        try:
            client.get(f"/repos/{repo.owner}/{repo.name}/contents/.github/workflows")
            has_workflows = True
        except GitHubError:
            has_workflows = False

    latest_conclusion = None
    days_since_run = None
    try:
        runs = client.get(
            f"/repos/{repo.owner}/{repo.name}/actions/runs",
            params={"per_page": 1, "branch": repo.default_branch},
        )
        items = runs.get("workflow_runs") or []
        if items:
            latest_conclusion = items[0].get("conclusion")
            created = items[0].get("created_at")
            if created:
                from datetime import UTC, datetime

                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                days_since_run = max(0, (datetime.now(UTC) - dt).days)
    except GitHubError:
        pass

    return {
        "has_workflows": has_workflows,
        "latest_conclusion": latest_conclusion,
        "latest_failed": latest_conclusion == "failure",
        "days_since_run": days_since_run,
    }
