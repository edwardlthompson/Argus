"""GitHub Issues API helpers for Argus inbox sync."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.inbox_format import (
    DONE_COMMENT,
    build_issue_body,
    build_issue_title,
    parse_marker,
)
from argus.models import MatchedFix
from argus.state import StateStore
from argus.status_page import is_security_fix


def ensure_labels(client: GitHubClient, owner: str, name: str, labels: list[str]) -> None:
    for label in labels:
        try:
            client.post(
                f"/repos/{owner}/{name}/labels",
                allow_write=True,
                json={"name": label, "color": "0f6b5c"},
            )
        except GitHubError as exc:
            if "422" not in str(exc):
                raise


def list_inbox_issues(
    client: GitHubClient,
    owner: str,
    name: str,
    label: str,
    *,
    state: str,
    max_pages: int = 20,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    page = 1
    while page <= max_pages:
        batch = client.get(
            f"/repos/{owner}/{name}/issues",
            params={"state": state, "labels": label, "per_page": 100, "page": page},
        )
        if not batch:
            break
        issues.extend(i for i in batch if "pull_request" not in i)
        if len(batch) < 100:
            break
        page += 1
    return issues


def has_done_comment(client: GitHubClient, owner: str, name: str, number: int) -> bool:
    comments = client.get(
        f"/repos/{owner}/{name}/issues/{number}/comments",
        params={"per_page": 50},
    )
    needle = DONE_COMMENT.lower()
    for c in comments or []:
        body = (c.get("body") or "").strip().lower()
        if body == needle or needle in body.split():
            return True
    return False


def apply_inbox_mutations(
    client: GitHubClient,
    store: StateStore,
    *,
    owner: str,
    name: str,
    label_inbox: str,
    label_security: str,
    open_desired: dict[tuple[str, str], tuple[str, MatchedFix]],
    max_issues: int,
    created: list[str],
    updated: list[str],
    resolved: list[str],
) -> None:
    labels_needed = [label_inbox]
    if any(is_security_fix(k[0]) for k in open_desired):
        labels_needed.append(label_security)
    ensure_labels(client, owner, name, labels_needed)

    open_issues = list_inbox_issues(client, owner, name, label_inbox, state="open")
    by_marker: dict[tuple[str, str], dict[str, Any]] = {}
    for issue in open_issues:
        parsed = parse_marker(issue.get("body") or "")
        if parsed:
            by_marker[parsed] = issue

    for issue in list_inbox_issues(
        client, owner, name, label_inbox, state="closed", max_pages=3
    ):
        parsed = parse_marker(issue.get("body") or "")
        if not parsed:
            continue
        fix_id, repo = parsed
        if not store.is_resolved(repo, fix_id):
            store.record_resolution(repo, fix_id, ttl_days=30, source="inbox_issue")
            resolved.append(f"{fix_id}:{repo}")

    for issue in open_issues:
        parsed = parse_marker(issue.get("body") or "")
        if not parsed:
            continue
        fix_id, repo = parsed
        number = int(issue["number"])
        if has_done_comment(client, owner, name, number):
            store.record_resolution(repo, fix_id, ttl_days=30, source="inbox_done")
            client.patch(
                f"/repos/{owner}/{name}/issues/{number}",
                allow_write=True,
                json={"state": "closed"},
            )
            resolved.append(f"{fix_id}:{repo}")
            by_marker.pop(parsed, None)

    created_count = 0
    for key, (repo_full, matched) in open_desired.items():
        if created_count >= max_issues and key not in by_marker:
            break
        title = build_issue_title(matched, repo_full)
        body = build_issue_body(matched, repo_full)
        labels = [label_inbox]
        if is_security_fix(matched.fix.id):
            labels.append(label_security)
        existing = by_marker.get(key)
        if existing:
            client.patch(
                f"/repos/{owner}/{name}/issues/{existing['number']}",
                allow_write=True,
                json={"title": title, "body": body, "labels": labels},
            )
            updated.append(f"{key[0]}:{key[1]}")
        else:
            client.post(
                f"/repos/{owner}/{name}/issues",
                allow_write=True,
                json={"title": title, "body": body, "labels": labels},
            )
            created.append(f"{key[0]}:{key[1]}")
            created_count += 1
