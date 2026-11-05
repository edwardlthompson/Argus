"""Security posture signals."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    secret_scanning = False
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}")
        # secret_scanning is not always present; treat presence of security_and_analysis if available
        saa = data.get("security_and_analysis") or {}
        secret_scanning = bool((saa.get("secret_scanning") or {}).get("status") == "enabled")
    except GitHubError:
        secret_scanning = False

    codeql_likely = False
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/contents/.github/workflows/codeql.yml")
        codeql_likely = True
    except GitHubError:
        try:
            client.get(
                f"/repos/{repo.owner}/{repo.name}/contents/.github/workflows/codeql.yaml"
            )
            codeql_likely = True
        except GitHubError:
            codeql_likely = False

    return {
        "secret_scanning_enabled": secret_scanning,
        "private": repo.private,
        "archived": repo.archived,
        "codeql_likely": codeql_likely,
    }
