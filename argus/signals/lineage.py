"""Parent-template lineage signals (.template-version vs upstream)."""

from __future__ import annotations

import base64
from typing import Any

from argus.config_loader import load_yaml
from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord
from argus.paths import CONFIG_DIR


def _parent_cfg() -> dict[str, Any]:
    path = CONFIG_DIR / "parent.yaml"
    if not path.exists():
        return {
            "upstream": "edwardlthompson/agent-project-bootstrap",
            "expected_version": "1.12.0",
            "lineage_files": [".template-version"],
        }
    return load_yaml(path)


def _read_file(client: GitHubClient, repo: RepoRecord, path: str) -> str | None:
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        if isinstance(data, dict) and data.get("encoding") == "base64" and data.get("content"):
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return None
    except GitHubError:
        return None


def _parse_semver(text: str) -> tuple[int, ...]:
    core = text.strip().lstrip("v").split("-")[0]
    parts: list[int] = []
    for p in core.split("."):
        if p.isdigit():
            parts.append(int(p))
        else:
            break
    return tuple(parts) if parts else (0,)


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    cfg = _parent_cfg()
    expected = str(cfg.get("expected_version", "0.0.0"))
    upstream = str(cfg.get("upstream", ""))
    version_raw = _read_file(client, repo, ".template-version")
    update_raw = _read_file(client, repo, ".template-update.json")
    template_version = version_raw.strip() if version_raw else None
    points_upstream = bool(update_raw and upstream and upstream in update_raw)
    agents = _read_file(client, repo, "AGENTS.md")
    mentions_parent = bool(agents and upstream and upstream in agents)
    is_child = bool(template_version or points_upstream or mentions_parent)

    missing: list[str] = []
    for path in cfg.get("lineage_files") or [".template-version"]:
        if _read_file(client, repo, str(path)) is None:
            missing.append(str(path))

    version_behind = False
    if template_version:
        version_behind = _parse_semver(template_version) < _parse_semver(expected)

    return {
        "is_template_child": is_child,
        "has_template_version": template_version is not None,
        "template_version": template_version,
        "expected_version": expected,
        "upstream": upstream,
        "version_behind": version_behind,
        "missing_lineage_files": missing,
        "points_upstream": points_upstream,
    }
