"""Open / stale pull request signals."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord


def _classify_pr(pr: dict[str, Any]) -> str:
    login = str(((pr.get("user") or {}).get("login")) or "").lower()
    title = str(pr.get("title") or "").lower()
    if login in {"dependabot[bot]", "dependabot"}:
        return "dependabot"
    if (
        login in {"github-actions[bot]", "release-please[bot]"}
        or title.startswith("chore(main): release")
        or title.startswith("chore: release")
    ):
        return "release"
    return "feature"


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    try:
        pulls = client.get(
            f"/repos/{repo.owner}/{repo.name}/pulls",
            params={"state": "open", "per_page": 100},
        )
    except GitHubError:
        return {
            "open_prs": 0,
            "stale_prs_30d": 0,
            "failed_check_prs": 0,
            "dependabot_prs": 0,
            "release_prs": 0,
            "feature_prs": 0,
        }

    now = datetime.now(UTC)
    stale = 0
    dep_n = 0
    rel_n = 0
    feat_n = 0
    for pr in pulls:
        updated = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
        if (now - updated).days >= 30:
            stale += 1
        kind = _classify_pr(pr)
        if kind == "dependabot":
            dep_n += 1
        elif kind == "release":
            rel_n += 1
        else:
            feat_n += 1
    return {
        "open_prs": len(pulls),
        "stale_prs_30d": stale,
        "draft_prs": sum(1 for p in pulls if p.get("draft")),
        "dependabot_prs": dep_n,
        "release_prs": rel_n,
        "feature_prs": feat_n,
    }
