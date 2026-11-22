"""Presentation: description, topics, README hints."""

from __future__ import annotations

import base64
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord

GENERIC_TOPICS = frozenset(
    {"foss", "mit", "open-source", "opensource", "github", "repo", "project"}
)


def _readme_has_what_not(readme: Any) -> bool:
    if not isinstance(readme, dict):
        return False
    if readme.get("has_what_not_section"):
        return True
    content = readme.get("content")
    if isinstance(content, str) and content:
        try:
            text = (
                base64.b64decode(content).decode("utf-8", errors="replace")
                if readme.get("encoding") == "base64"
                else content
            )
            return "what this is not" in text.lower()
        except ValueError:
            return False
    return False


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
    has_what_not = False
    try:
        readme = client.get(f"/repos/{repo.owner}/{repo.name}/readme")
        has_readme = True
        has_what_not = _readme_has_what_not(readme)
    except GitHubError:
        has_readme = False
        has_what_not = False
    return {
        "description": desc,
        "description_len": len(desc),
        "topics": topics,
        "specific_topic_count": len(specific),
        "has_readme": has_readme,
        "has_what_not_section": has_what_not,
    }
