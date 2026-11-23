"""CI presence and recent run health on default branch."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord

_HOUSEKEEPING_WORKFLOWS = (
    "release please",
    "release",
    "sync build_plan",
    "auto-merge",
    "queue release please",
    "queue ready cursor",
    "weekly health",
    "weekly-health-check",
    "pages build and deployment",
    "deploy github pages",
)


def _is_housekeeping_run(run: dict[str, Any]) -> bool:
    name = str(run.get("name") or "").strip().lower()
    return any(name == h or name.startswith(h) or h in name for h in _HOUSEKEEPING_WORKFLOWS)


def _pick_ci_run(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    completed = [r for r in items if (r.get("status") or "").lower() == "completed" or r.get("conclusion")]
    pool = completed or items
    non_hk = [run for run in pool if not _is_housekeeping_run(run)]
    if non_hk:
        top = non_hk[0]
        top_sha = top.get("head_sha")
        if top_sha and top.get("conclusion") == "failure":
            for run in non_hk:
                if run.get("head_sha") == top_sha and run.get("conclusion") == "success":
                    return run
        return top
    return pool[0]


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
            params={"per_page": 10, "branch": repo.default_branch},
        )
        items = runs.get("workflow_runs") or []
        picked = _pick_ci_run(items)
        if picked:
            latest_conclusion = picked.get("conclusion")
            created = picked.get("created_at")
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
