"""Hygiene: license, community files, linguist attributes."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    license_ok = False
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/license")
        license_ok = bool(data.get("license"))
    except GitHubError:
        license_ok = False

    files = {
        "security_md": _exists(client, repo, "SECURITY.md"),
        "contributing_md": _exists(client, repo, "CONTRIBUTING.md"),
        "code_of_conduct_md": _exists(client, repo, "CODE_OF_CONDUCT.md"),
        "gitattributes": _exists(client, repo, ".gitattributes"),
        "license_file": license_ok
        or _exists(client, repo, "LICENSE")
        or _exists(client, repo, "LICENSE.md"),
        "agent_files_at_root": _exists(client, repo, "AGENT_MEMORY.md"),
    }
    return files


def _exists(client: GitHubClient, repo: RepoRecord, path: str) -> bool:
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        return True
    except GitHubError:
        return False
