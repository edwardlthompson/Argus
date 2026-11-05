"""Dependency / Dependabot signals."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    dependabot = False
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/vulnerability-alerts")
        dependabot = True
    except GitHubError as exc:
        msg = str(exc)
        if "204" in msg or "-> 204" in msg:
            dependabot = True
        elif "404" in msg:
            dependabot = False
        else:
            # Permission errors → unknown, still return structured data
            dependabot = False
    open_alerts = 0
    try:
        alerts = client.get(
            f"/repos/{repo.owner}/{repo.name}/dependabot/alerts",
            params={"state": "open", "per_page": 10},
        )
        if isinstance(alerts, list):
            open_alerts = len(alerts)
    except GitHubError:
        open_alerts = 0

    return {
        "vulnerability_alerts_enabled": dependabot,
        "has_dependabot_config": _has_file(client, repo, ".github/dependabot.yml")
        or _has_file(client, repo, ".github/dependabot.yaml"),
        "open_dependabot_alerts": open_alerts,
    }


def _has_file(client: GitHubClient, repo: RepoRecord, path: str) -> bool:
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        return True
    except GitHubError:
        return False
