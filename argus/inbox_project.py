"""Optional GitHub Projects v2 sync for open argus-inbox Issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from argus.config_loader import load_inbox
from argus.github_client import GitHubClient, GitHubError

_FIND = (
    "query($login:String!,$number:Int!){user(login:$login){projectV2(number:$number){id}}"
    "organization(login:$login){projectV2(number:$number){id}}}"
)
_LIST = (
    "query($projectId:ID!,$cursor:String){node(id:$projectId){...on ProjectV2{"
    "items(first:100,after:$cursor){pageInfo{hasNextPage endCursor}"
    "nodes{id content{...on Issue{id number}}}}}}}"
)
_ADD = (
    "mutation($projectId:ID!,$contentId:ID!){"
    "addProjectV2ItemById(input:{projectId:$projectId,contentId:$contentId}){item{id}}}"
)


@dataclass
class ProjectSyncResult:
    added: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run_would_add: list[str] = field(default_factory=list)


def _project_id(client: GitHubClient, login: str, number: int) -> str | None:
    data = client.graphql(_FIND, {"login": login, "number": number})
    user = (data.get("user") or {}).get("projectV2") or {}
    org = (data.get("organization") or {}).get("projectV2") or {}
    return user.get("id") or org.get("id")


def _existing_ids(client: GitHubClient, project_id: str) -> set[str]:
    found: set[str] = set()
    cursor: str | None = None
    while True:
        data = client.graphql(_LIST, {"projectId": project_id, "cursor": cursor})
        items = ((data.get("node") or {}).get("items")) or {}
        for node in items.get("nodes") or []:
            iid = (node.get("content") or {}).get("id")
            if iid:
                found.add(str(iid))
        page = items.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            break
        cursor = page.get("endCursor")
    return found


def sync_inbox_project(
    client: GitHubClient,
    *,
    dry_run: bool = True,
    config: dict[str, Any] | None = None,
    issue_nodes: list[dict[str, Any]] | None = None,
) -> ProjectSyncResult:
    """Add open inbox Issues to Projects v2 when ``project_number`` is set."""
    cfg = config or load_inbox()
    result = ProjectSyncResult()
    number = cfg.get("project_number")
    if number is None:
        return result
    try:
        number = int(number)
    except (TypeError, ValueError):
        result.errors.append("inbox.project_number must be an int")
        return result

    controller = str(cfg.get("controller_repo") or "")
    if "/" not in controller:
        result.errors.append("inbox.controller_repo missing")
        return result
    owner, name = controller.split("/", 1)
    project_login = str(cfg.get("project_owner") or owner)
    label = str(cfg.get("label_inbox") or "argus-inbox")

    try:
        project_id = _project_id(client, project_login, number)
    except GitHubError as exc:
        result.errors.append(str(exc))
        return result
    if not project_id:
        result.errors.append(f"project #{number} not found for {project_login}")
        return result

    if issue_nodes is None:
        try:
            issues = client.get(
                f"/repos/{owner}/{name}/issues",
                params={"state": "open", "labels": label, "per_page": 100},
            )
        except GitHubError as exc:
            result.errors.append(str(exc))
            return result
        issue_nodes = [
            {"id": i.get("node_id"), "number": i.get("number")}
            for i in (issues or [])
            if i.get("node_id") and i.get("number") is not None
        ]

    try:
        existing = _existing_ids(client, project_id)
    except GitHubError as exc:
        result.errors.append(str(exc))
        return result

    for issue in issue_nodes:
        node_id = str(issue.get("id") or "")
        key = f"#{issue.get('number')}"
        if not node_id:
            continue
        if node_id in existing:
            result.skipped.append(key)
            continue
        if dry_run:
            result.dry_run_would_add.append(key)
            continue
        try:
            client.graphql(_ADD, {"projectId": project_id, "contentId": node_id}, allow_write=True)
            result.added.append(key)
        except GitHubError as exc:
            result.errors.append(f"{key}: {exc}")
    return result


def summarize_project(result: ProjectSyncResult) -> dict[str, Any]:
    return {
        "added": result.added,
        "skipped": result.skipped,
        "dry_run_would_add": result.dry_run_would_add,
        "errors": result.errors,
    }
