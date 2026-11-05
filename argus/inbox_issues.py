"""Sync human tasks to GitHub Issues on the controller repo (private control plane)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from argus.config_loader import load_inbox
from argus.github_client import GitHubClient, GitHubError
from argus.inbox_api import apply_inbox_mutations
from argus.inbox_format import build_issue_body, build_issue_title, issue_marker, parse_marker
from argus.models import MatchedFix, RepoPlan
from argus.state import StateStore
from argus.status_page import is_security_fix

__all__ = [
    "InboxSyncResult",
    "build_issue_body",
    "build_issue_title",
    "issue_marker",
    "parse_marker",
    "summarize_inbox",
    "sync_inbox_issues",
]


@dataclass
class InboxSyncResult:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    resolved: list[str] = field(default_factory=list)
    skipped_security: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def sync_inbox_issues(
    client: GitHubClient,
    store: StateStore,
    plans: list[RepoPlan],
    *,
    dry_run: bool = True,
    config: dict[str, Any] | None = None,
) -> InboxSyncResult:
    cfg = config or load_inbox()
    result = InboxSyncResult()
    if not cfg.get("enabled", True):
        return result

    controller = str(cfg.get("controller_repo") or "")
    if "/" not in controller:
        result.errors.append("inbox.controller_repo missing")
        return result
    owner, name = controller.split("/", 1)
    label_inbox = str(cfg.get("label_inbox") or "argus-inbox")
    label_security = str(cfg.get("label_security") or "argus-security")
    security_issues = bool(cfg.get("security_issues", False))
    max_issues = int(cfg.get("max_issues_per_run") or 20)

    open_desired: dict[tuple[str, str], tuple[str, MatchedFix]] = {}
    for plan in plans:
        for matched in plan.human_fixes:
            key = (matched.fix.id, plan.repo.full_name)
            if is_security_fix(matched.fix.id) and not security_issues:
                result.skipped_security.append(f"{matched.fix.id}:{plan.repo.full_name}")
                continue
            open_desired[key] = (plan.repo.full_name, matched)

    if dry_run:
        for key in list(open_desired)[:max_issues]:
            result.updated.append(f"dry-run:{key[0]}:{key[1]}")
        return result

    try:
        apply_inbox_mutations(
            client,
            store,
            owner=owner,
            name=name,
            label_inbox=label_inbox,
            label_security=label_security,
            open_desired=open_desired,
            max_issues=max_issues,
            created=result.created,
            updated=result.updated,
            resolved=result.resolved,
        )
    except GitHubError as exc:
        result.errors.append(str(exc))
    return result


def summarize_inbox(result: InboxSyncResult) -> dict[str, Any]:
    return {
        "created": result.created,
        "updated": result.updated,
        "resolved": result.resolved,
        "skipped_security": result.skipped_security,
        "errors": result.errors,
    }
