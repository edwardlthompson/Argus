"""Worktree GC, gate-fail Issues, prompt budget helpers."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from argus.config_loader import load_inbox
from argus.github_client import GitHubClient
from argus.paths import DATA_DIR


def gc_worktrees(*, apply: bool = False, root: Path | None = None) -> dict[str, Any]:
    base = root or (DATA_DIR / "worktrees")
    if not base.exists():
        return {"removed": [], "kept": [], "apply": apply}
    removed: list[str] = []
    kept: list[str] = []
    for path in sorted(base.iterdir()):
        if not path.is_dir():
            continue
        if apply:
            shutil.rmtree(path, ignore_errors=True)
            removed.append(path.name)
        else:
            kept.append(path.name)
    return {"removed": removed, "kept": kept if not apply else [], "apply": apply}


def prompt_budget_report(prompts: dict[str, str], max_chars: int) -> dict[str, Any]:
    rows = [
        {"repo": repo, "chars": len(text), "over_budget": len(text) > max_chars}
        for repo, text in prompts.items()
    ]
    return {"max_chars": max_chars, "prompts": rows}


def open_gate_failure_issue(
    client: GitHubClient, *, title: str, body: str, dry_run: bool = True
) -> str | None:
    cfg = load_inbox()
    controller = str(cfg.get("controller_repo") or "")
    if "/" not in controller:
        return None
    owner, name = controller.split("/", 1)
    if dry_run:
        return f"dry-run:{owner}/{name}"
    issue = client.post(
        f"/repos/{owner}/{name}/issues",
        allow_write=True,
        json={
            "title": title[:200],
            "body": body[:6000],
            "labels": [str(cfg.get("label_inbox") or "argus-inbox"), "argus-gate-fail"],
        },
    )
    return str(issue.get("html_url") or "")
