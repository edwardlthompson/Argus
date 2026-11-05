"""Apply profile Overview README to public USERNAME/USERNAME via PR or create."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoPlan
from argus.profile_featured import enrich_plans_for_profile
from argus.profile_github import ensure_profile_repo, get_readme, open_readme_pr
from argus.profile_readme import (
    compose_profile_readme,
    load_profile_readme_config,
    needs_profile_update,
)
from argus.state import StateStore


@dataclass
class ProfileApplyResult:
    action: str = "skipped"
    url: str | None = None
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def sync_profile_readme(
    client: GitHubClient,
    store: StateStore,
    plans: list[RepoPlan],
    *,
    dry_run: bool = True,
    user: dict[str, Any] | None = None,
) -> ProfileApplyResult:
    cfg = load_profile_readme_config()
    result = ProfileApplyResult()
    if not cfg.get("enabled", True):
        result.detail = "disabled"
        return result
    if client.report_only:
        result.detail = "report_only"
        return result

    try:
        me = user or client.whoami()
    except GitHubError as exc:
        result.errors.append(str(exc))
        return result
    login = str(me.get("login") or "")
    if not login:
        result.detail = "no_login"
        return result

    enrich_plans_for_profile(client, plans)
    body = compose_profile_readme(user=me, plans=plans, config=cfg)
    if dry_run:
        result.action = "dry_run"
        result.detail = f"would_update:{login}/{login} chars={len(body)}"
        return result

    try:
        ensure_profile_repo(client, login)
        existing, sha = get_readme(client, login)
        if not needs_profile_update(existing, body):
            result.action = "unchanged"
            store.record_resolution(
                f"{login}/{login}", "PROF-README", ttl_days=7, source="profile"
            )
            return result
        url = open_readme_pr(
            client,
            login,
            body,
            sha=sha,
            display_name=str(me.get("name") or login),
            tagline=str(cfg.get("tagline") or ""),
        )
        result.action = "pr"
        result.url = url
        store.record_resolution(
            f"{login}/{login}", "PROF-README", ttl_days=7, source="profile"
        )
    except GitHubError as exc:
        result.errors.append(str(exc))
    return result
