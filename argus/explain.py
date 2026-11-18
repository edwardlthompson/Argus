"""Explain attention score for one repo (read-only)."""

from __future__ import annotations

from typing import Any

from argus.config_loader import load_rubric
from argus.github_client import GitHubClient
from argus.models import RepoRecord, RepoStatus
from argus.score import score_repo
from argus.signals import collect_signals


def explain_repo(client: GitHubClient, full_name: str) -> dict[str, Any]:
    if "/" not in full_name:
        raise ValueError("repo must be owner/name")
    owner, name = full_name.split("/", 1)
    raw = client.get_repo(owner, name)
    status = RepoStatus.ARCHIVED if raw.get("archived") else RepoStatus.ACTIVE
    repo = RepoRecord(
        full_name=full_name,
        owner=owner,
        name=name,
        status=status,
        private=bool(raw.get("private")),
        archived=bool(raw.get("archived")),
        fork=bool(raw.get("fork")),
        description=raw.get("description"),
        default_branch=raw.get("default_branch") or "main",
        html_url=raw.get("html_url") or "",
        topics=list(raw.get("topics") or []),
        raw=raw,
    )
    signals = collect_signals(client, repo)
    result = score_repo(signals, load_rubric(), status)
    return {
        "repo": full_name,
        "attention": result.attention,
        "confidence": result.confidence.value,
        "category_scores": result.category_scores,
        "notes": result.notes,
        "signals": signals.as_dict(),
    }
