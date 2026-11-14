"""BUILD_PLAN board shape vs agent-project-bootstrap BUILD_PLAN_TEMPLATE.md."""

from __future__ import annotations

import base64
from typing import Any

from argus.board_classify import classify_board, locate_board_path
from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord


def _read_text(client: GitHubClient, repo: RepoRecord, path: str) -> str | None:
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
    except GitHubError:
        return None
    if not isinstance(data, dict) or not data.get("content"):
        return None
    try:
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except (TypeError, ValueError):
        return None


def _exists(client: GitHubClient, repo: RepoRecord, path: str) -> bool:
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        return True
    except GitHubError:
        return False


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    root = _read_text(client, repo, "BUILD_PLAN.md")
    docs = None if root is not None else _read_text(client, repo, "docs/BUILD_PLAN.md")
    path = locate_board_path(root_exists=root is not None, docs_exists=docs is not None)
    text = root if root is not None else docs
    info = classify_board(text, path)
    info["has_board"] = path is not None
    info["has_completed_tasks"] = _exists(client, repo, "COMPLETED_TASKS.md") or _exists(
        client, repo, "docs/COMPLETED_TASKS.md"
    )
    return info
