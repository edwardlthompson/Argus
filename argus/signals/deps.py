"""Dependency / Dependabot signals."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord

# GitHub pauses Dependabot alerts after ~365d with no activity (push re-enables).
# Flag at 300d so operators act before the silent pause.
_ALERT_PAUSE_RISK_DAYS = 300


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

    days = _days_since_push(repo)
    return {
        "vulnerability_alerts_enabled": dependabot,
        "has_dependabot_config": _has_file(client, repo, ".github/dependabot.yml")
        or _has_file(client, repo, ".github/dependabot.yaml"),
        "open_dependabot_alerts": open_alerts,
        "days_since_push": days,
        "dependabot_alert_pause_risk": bool(
            days is not None and days >= _ALERT_PAUSE_RISK_DAYS
        ),
        "dependabot_alert_pause_risk_days": _ALERT_PAUSE_RISK_DAYS,
    }


def _days_since_push(repo: RepoRecord) -> int | None:
    pushed = (repo.raw or {}).get("pushed_at")
    if not pushed:
        return None
    try:
        dt = datetime.fromisoformat(str(pushed).replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, (datetime.now(UTC) - dt).days)


def _has_file(client: GitHubClient, repo: RepoRecord, path: str) -> bool:
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        return True
    except GitHubError:
        return False
