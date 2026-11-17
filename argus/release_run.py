"""Local `argus releases` orchestration (REST only; never GitHub Actions)."""

from __future__ import annotations

import os
from typing import Any

from argus.config_loader import load_status
from argus.discover import _to_record, discover_portfolio
from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord, RepoStatus
from argus.release_detect import cfg, use_authenticated_owner
from argus.release_prep import apply_prep, plan_prep
from argus.release_report import grandma_lines, write_reports
from argus.release_scan import collect_repo
from argus.state import StateStore


def _token() -> str:
    return (os.environ.get("ARGUS_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()


def _list_repos(
    client: GitHubClient,
    store: StateStore,
    *,
    owner: str | None,
    repo: str | None,
    public_only: bool,
) -> tuple[list[RepoRecord], str]:
    declared = load_status()
    if repo:
        owner_n, name = repo.split("/", 1)
        raw = client.get_repo(owner_n, name)
        status = declared.get(raw["full_name"], RepoStatus.ARCHIVED if raw.get("archived") else RepoStatus.ACTIVE)
        return [_to_record(raw, status)], "single"
    if owner:
        login = None
        try:
            login = str((client.whoami() or {}).get("login") or "") or None
        except GitHubError:
            login = None
        listing = "user_public"
        if use_authenticated_owner(owner, login, public_only=public_only):
            raws = client.list_viewer_repos(affiliation="owner")
            listing = "viewer"
        else:
            raws = client.list_user_repos(owner, public_only=True)
        if public_only:
            raws = [r for r in raws if not r.get("private")]
            listing = "user_public"
        out: list[RepoRecord] = []
        for raw in raws:
            if raw.get("archived"):
                continue
            status = declared.get(raw["full_name"], RepoStatus.ACTIVE)
            if status == RepoStatus.ARCHIVED:
                continue
            out.append(_to_record(raw, status))
        return out, listing
    return list(discover_portfolio(client, store, public_only=public_only).repos), "portfolio"


def run_releases(
    *,
    dry_run: bool = True,
    open_prs: bool = False,
    owner: str | None = None,
    repo: str | None = None,
    public_only: bool = False,
    max_prs: int | None = None,
    notify: bool = False,
) -> dict[str, Any]:
    c = cfg()
    if not c.get("enabled", True):
        return {"enabled": False, "rows": [], "flagged": []}
    token = _token()
    if not token:
        raise SystemExit("GITHUB_TOKEN or ARGUS_GITHUB_TOKEN is not set")
    live = bool(open_prs or c.get("open_prs")) and not dry_run
    cap = int(max_prs if max_prs is not None else (c.get("max_prs_per_run") or 5))
    store = StateStore()
    rows: list[dict[str, Any]] = []
    opened = 0
    listing = "unknown"
    try:
        with GitHubClient(token=token, report_only=False) as client:
            repos, listing = _list_repos(client, store, owner=owner, repo=repo, public_only=public_only)
            for rec in repos:
                row = collect_repo(client, rec, c)
                if row.get("needs_prep") and not row.get("irregular"):
                    plan = plan_prep(row, c)
                    if live and opened >= cap:
                        row["pr_action"] = "max_prs"
                    elif plan.files:
                        result = apply_prep(client, rec, plan, dry_run=not live)
                        row["pr_action"] = result.get("action")
                        row["pr_url"] = result.get("pr") or None
                        row["tag_cmd"] = plan.tag_cmd
                        if live and result.get("action") in {"opened", "updated", "existing"}:
                            opened += 1
                    else:
                        row["pr_action"] = "no_files"
                elif row.get("irregular"):
                    row["pr_action"] = "irregular"
                rows.append(row)
    finally:
        store.close()
    flagged = [r for r in rows if r.get("needs_prep")]
    paths = write_reports(rows, dry_run=not live, listing=listing)
    digest = grandma_lines(flagged)
    if notify and digest:
        from argus.config_loader import load_notifications
        from argus.notify import _merge_env
        from argus.notify_channels import dispatch_message

        text = "Argus release freshness:\n" + "\n".join(digest[:20])
        dispatch_message(text, _merge_env(load_notifications()))
    return {
        "enabled": True,
        "dry_run": not live,
        "listing": listing,
        "repos": len(rows),
        "flagged": len(flagged),
        "opened_or_updated": opened,
        "grandma": digest,
        "artifacts": {k: str(v) for k, v in paths.items()},
        "rows": [
            {k: r.get(k) for k in (
                "full_name", "platforms", "latest_tag", "latest_date", "missing",
                "visibility", "skip", "needs_prep", "irregular", "irregular_reason",
                "pr_action", "pr_url", "tag_cmd",
            )}
            for r in rows
        ],
    }
