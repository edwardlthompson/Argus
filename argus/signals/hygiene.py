"""Hygiene: license SPDX, community files, stale branches, CODEOWNERS."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord

_STALE_DAYS = 90


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    spdx: str | None = None
    license_ok = False
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/license")
        lic = data.get("license") or {}
        spdx = lic.get("spdx_id")
        license_ok = bool(lic)
    except GitHubError:
        pass

    return {
        "security_md": _exists(client, repo, "SECURITY.md"),
        "contributing_md": _exists(client, repo, "CONTRIBUTING.md"),
        "code_of_conduct_md": _exists(client, repo, "CODE_OF_CONDUCT.md"),
        "codeowners": _exists(client, repo, "CODEOWNERS")
        or _exists(client, repo, ".github/CODEOWNERS")
        or _exists(client, repo, "docs/CODEOWNERS"),
        "gitattributes": _exists(client, repo, ".gitattributes"),
        "gitignore": _exists(client, repo, ".gitignore"),
        "license_file": license_ok
        or _exists(client, repo, "LICENSE")
        or _exists(client, repo, "LICENSE.md"),
        "agent_files_at_root": _exists(client, repo, "AGENT_MEMORY.md"),
        "license_spdx": spdx,
        "stale_branch_count": _stale_branches(client, repo),
        "branch_protection": _branch_protection(client, repo),
        "actions_runs_30d": _actions_runs(client, repo),
    }


def _exists(client: GitHubClient, repo: RepoRecord, path: str) -> bool:
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        return True
    except GitHubError:
        return False


def _stale_branches(client: GitHubClient, repo: RepoRecord) -> int:
    try:
        branches = client.get(
            f"/repos/{repo.owner}/{repo.name}/branches",
            params={"per_page": 30},
        )
    except GitHubError:
        return 0
    now = datetime.now(UTC)
    stale = 0
    default = repo.default_branch
    for br in branches or []:
        name = br.get("name") or ""
        if name == default:
            continue
        try:
            commit = client.get(
                f"/repos/{repo.owner}/{repo.name}/commits/{br.get('commit', {}).get('sha', name)}"
            )
            date_s = ((commit.get("commit") or {}).get("committer") or {}).get("date")
            if not date_s:
                continue
            when = datetime.fromisoformat(date_s.replace("Z", "+00:00"))
            if (now - when).days >= _STALE_DAYS:
                stale += 1
        except (GitHubError, TypeError, ValueError):
            continue
    return stale


def _branch_protection(client: GitHubClient, repo: RepoRecord) -> bool | None:
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/branches/{repo.default_branch}/protection")
        return True
    except GitHubError as exc:
        if "404" in str(exc):
            return False
        return None


def _actions_runs(client: GitHubClient, repo: RepoRecord) -> int | None:
    """Heuristic: workflow runs in last page (cost proxy, not billing API)."""
    try:
        data = client.get(
            f"/repos/{repo.owner}/{repo.name}/actions/runs",
            params={"per_page": 30},
        )
        return int(data.get("total_count") or len(data.get("workflow_runs") or []))
    except GitHubError:
        return None
