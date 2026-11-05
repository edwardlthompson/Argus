"""Portfolio discovery and change detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from argus.config_loader import load_allowlist, load_status
from argus.github_client import GitHubClient
from argus.models import RepoRecord, RepoStatus
from argus.state import StateStore, sync_status_yaml


@dataclass
class DiscoveryResult:
    repos: list[RepoRecord]
    new: list[str]
    removed: list[str]
    viewer: str | None
    report_only: bool = False
    skipped_archived: list[str] | None = None

def _to_record(raw: dict[str, Any], status: RepoStatus) -> RepoRecord:
    full = raw["full_name"]
    owner, name = full.split("/", 1)
    perms = raw.get("permissions") or {}
    return RepoRecord(
        full_name=full,
        owner=owner,
        name=name,
        status=status,
        private=bool(raw.get("private")),
        archived=bool(raw.get("archived")),
        fork=bool(raw.get("fork")),
        description=raw.get("description"),
        default_branch=raw.get("default_branch") or "main",
        html_url=raw.get("html_url") or "",
        permissions={k: bool(v) for k, v in perms.items()},
        topics=list(raw.get("topics") or []),
        raw=raw,
    )

def _allowed(full_name: str, owner: str, viewer: str | None, allow: dict[str, Any]) -> bool:
    if full_name in (allow.get("deny") or []):
        return False
    mode = allow.get("mode", "owner_only")
    allow_list = allow.get("allow") or []
    orgs = {str(o).lower() for o in (allow.get("orgs") or [])}
    if mode == "allowlist":
        return full_name in allow_list
    if mode == "org":
        if orgs and owner.lower() not in orgs:
            return False
        return full_name in allow_list if allow_list else bool(orgs)
    if mode == "collaborator":
        return True
    if mode == "owner_only":
        if allow_list and full_name in allow_list:
            return True
        return viewer is not None and owner.lower() == viewer.lower()
    return full_name in allow_list if allow_list else True

def _portfolio_raw(client: GitHubClient, allow: dict[str, Any], *, public_only: bool) -> list[dict[str, Any]]:
    mode = allow.get("mode", "owner_only")
    orgs = [str(o) for o in (allow.get("orgs") or [])]
    if mode == "org" and orgs:
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for org in orgs:
            for raw in client.list_org_repos(org, public_only=public_only):
                if raw["full_name"] not in seen:
                    seen.add(raw["full_name"])
                    out.append(raw)
        return out
    default_aff = "owner,collaborator,organization_member"
    if mode == "collaborator":
        default_aff = "collaborator,organization_member"
    return client.list_viewer_repos(affiliation=str(allow.get("affiliation") or default_aff))

def discover_portfolio(
    client: GitHubClient,
    store: StateStore,
    *,
    target: str | None = None,
    public_only: bool = False,
    include_archived: bool = False,
) -> DiscoveryResult:
    """Discover repos; allowlist ``mode: org|collaborator`` scopes portfolio listing."""
    declared = load_status()
    sync_status_yaml(store, declared)
    allow = load_allowlist()
    viewer: str | None = None
    report_only = False
    raw_repos: list[dict[str, Any]] = []

    if target:
        report_only = True
        client.report_only = True
        if "/" in target:
            owner, name = target.split("/", 1)
            raw_repos = [client.get_repo(owner, name)]
        else:
            try:
                raw_repos = client.list_org_repos(target, public_only=public_only)
            except Exception:  # noqa: BLE001
                raw_repos = client.list_user_repos(target, public_only=True or public_only)
    else:
        viewer = client.whoami().get("login")
        raw_repos = _portfolio_raw(client, allow, public_only=public_only)

    known = store.known_repos()
    known_names = set(known.keys())
    current_names: set[str] = set()
    repos: list[RepoRecord] = []
    skipped_archived: list[str] = []

    for raw in raw_repos:
        full = raw["full_name"]
        owner = full.split("/", 1)[0]
        if not target and not _allowed(full, owner, viewer, allow):
            continue
        current_names.add(full)
        if raw.get("archived"):
            status = RepoStatus.ARCHIVED
        elif full in declared:
            status = declared[full]
        elif full in known:
            status = known[full]["status"]
        else:
            status = RepoStatus.ACTIVE
        store.upsert_repo(full, status, {"html_url": raw.get("html_url") or ""})
        if not include_archived and (status == RepoStatus.ARCHIVED or bool(raw.get("archived"))):
            skipped_archived.append(full)
            continue
        record = _to_record(raw, status)
        if report_only:
            record.permissions = {}
        repos.append(record)

    new = sorted(current_names - known_names)
    removed = sorted(known_names - current_names) if not target else []
    for name in removed:
        store.mark_inactive(name)
    return DiscoveryResult(
        repos=repos,
        new=new,
        removed=removed,
        viewer=viewer,
        report_only=report_only,
        skipped_archived=sorted(skipped_archived),
    )
