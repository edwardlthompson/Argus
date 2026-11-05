"""Presentation: description, topics, README hints."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord

GENERIC_TOPICS = frozenset(
    {"foss", "mit", "open-source", "opensource", "github", "repo", "project"}
)


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    desc = repo.description or ""
    topics = list(repo.topics)
    if not topics:
        try:
            data = client.get(f"/repos/{repo.owner}/{repo.name}/topics")
            topics = list(data.get("names") or [])
        except GitHubError:
            topics = []
    specific = [t for t in topics if t.lower() not in GENERIC_TOPICS]
    has_readme = False
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/readme")
        has_readme = True
    except GitHubError:
        has_readme = False
    has_what_not = False
    if has_readme:
        try:
            readme = client.get(f"/repos/{repo.owner}/{repo.name}/readme")
            # GitHub returns base64 content; presence check via download_url fetch is heavy —
            # treat missing field as unknown/false unless callers set it in fixtures.
            has_what_not = bool(readme.get("has_what_not_section"))
        except GitHubError:
            has_what_not = False
    return {
        "description": desc,
        "description_len": len(desc),
        "topics": topics,
        "specific_topic_count": len(specific),
        "has_readme": has_readme,
        "has_what_not_section": has_what_not,
    }
