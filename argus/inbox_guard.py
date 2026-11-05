"""Warn when inbox/security settings are unsafe on a public controller."""

from __future__ import annotations

from typing import Any

from argus.config_loader import load_inbox
from argus.github_client import GitHubClient, GitHubError


def check_public_controller_risks(
    client: GitHubClient | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> list[str]:
    """Return human-readable problems (empty if OK)."""
    cfg = config or load_inbox()
    problems: list[str] = []
    controller = str(cfg.get("controller_repo") or "")
    security = bool(cfg.get("security_issues", False))
    if not controller or "/" not in controller or controller.startswith("YOUR_LOGIN"):
        if security:
            problems.append(
                "inbox.controller_repo is a placeholder while security_issues is true — "
                "run scripts/bootstrap-argus-runner.* or set a private controller_repo"
            )
        return problems

    if not security:
        return problems

    if client is None:
        problems.append(
            "security_issues is true but GitHub client unavailable to verify "
            f"{controller} is private"
        )
        return problems

    owner, name = controller.split("/", 1)
    try:
        repo = client.get(f"/repos/{owner}/{name}")
    except GitHubError as exc:
        problems.append(f"cannot verify controller {controller}: {exc}")
        return problems

    if not repo.get("private"):
        problems.append(
            f"security_issues is true but controller {controller} is PUBLIC — "
            "SEC-* Issue bodies would be world-readable. Use a private runner "
            "or set security_issues: false."
        )
    return problems
