"""Orphan / unused-path signals — stage one (no examples/)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord
from argus.paths import CONFIG_DIR

_SKIP = (".cursor/",)
_STAGE_SKIP = ("examples/",)


def _load_cfg() -> dict[str, Any]:
    path = CONFIG_DIR / "orphans.yaml"
    if not path.is_file():
        return {"classes": [], "skip_prefixes": list(_STAGE_SKIP) + list(_SKIP)}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def should_skip_path(path: str, cfg: dict[str, Any] | None = None) -> bool:
    raw = (cfg or _load_cfg()).get("skip_prefixes") or list(_STAGE_SKIP) + list(_SKIP)
    p = path.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return any(p.startswith(pref) for pref in raw)


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    """Remote lightweight probe: .goldenpath.json entrypoints if present."""
    cfg = _load_cfg()
    classes = [c.get("id") for c in (cfg.get("classes") or []) if c.get("id")]
    entrypoints: list[str] = []
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/.goldenpath.json")
        if isinstance(data, dict) and data.get("content"):
            import base64

            raw = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            gp = json.loads(raw)
            eps = gp.get("entrypoints") or gp.get("entries") or []
            if isinstance(eps, list):
                entrypoints = [str(x) for x in eps]
    except (GitHubError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return {
        "stage": int(cfg.get("stage") or 1),
        "classes": classes,
        "entrypoints": entrypoints,
        "findings": [],  # deep AST parsers land with parent rule sync (S11)
        "examples_skipped": True,
    }


def local_scan(root: Path, cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Local filesystem scan helper (tests / future fleet). Stage-one: no examples/."""
    cfg = cfg or _load_cfg()
    findings: list[dict[str, Any]] = []
    allow = set(cfg.get("allowlist") or [])
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if should_skip_path(rel, cfg) or rel in allow:
            continue
        # Stage one: report only when .goldenpath.json exists and file is outside entrypoints
        # and looks like a stray demo asset under docs/assets with zero refs — deferred.
        _ = rel
    return findings
