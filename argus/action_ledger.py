"""Append-only action ledger for YOLO/fleet/auto_safe (audit + undo spine)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from argus.apply_history import _put_file, _resolve_controller
from argus.config_loader import load_inbox
from argus.github_client import GitHubClient, GitHubError
from argus.paths import DIST_DIR, ensure_runtime_dirs

ACTIONS_JSONL = "actions.jsonl"
ACTIONS_MD = "ACTIONS_CHANGELOG.md"
REMOTE_DIR = "argus-history"


def append_action(
    *,
    actor: str,
    repo: str,
    action: str,
    detail: str = "",
    pr_url: str | None = None,
    sha_before: str | None = None,
    sha_after: str | None = None,
    brief_id: str | None = None,
    rule_sha: str | None = None,
    verify_result: str | None = None,
    dist_dir: Path | None = None,
) -> dict[str, Any]:
    ensure_runtime_dirs()
    out = dist_dir or DIST_DIR
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "actor": actor,
        "repo": repo,
        "action": action,
        "detail": detail,
        "pr_url": pr_url,
        "sha_before": sha_before,
        "sha_after": sha_after,
        "brief_id": brief_id,
        "rule_sha": rule_sha,
        "verify_result": verify_result,
    }
    jsonl = out / ACTIONS_JSONL
    with jsonl.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    md = out / ACTIONS_MD
    line = (
        f"- `{entry['ts']}` · **{actor}** · `{repo}` · {action}"
        + (f" · {detail}" if detail else "")
        + (f" · {pr_url}" if pr_url else "")
        + "\n"
    )
    prev = md.read_text(encoding="utf-8") if md.exists() else (
        "# Argus actions changelog\n\n"
        "Append-only record of automatic actions for audit and undo.\n\n"
    )
    md.write_text(prev + line, encoding="utf-8")
    return entry


def record_actions(
    apply_summary: dict[str, Any],
    *,
    actor: str = "auto_safe",
    brief_id: str | None = None,
) -> list[dict[str, Any]]:
    """Expand an apply summary into ledger rows."""
    rows: list[dict[str, Any]] = []
    for key in apply_summary.get("applied") or []:
        repo, _, fix = str(key).partition(":")
        rows.append(
            append_action(
                actor=actor,
                repo=repo or "unknown",
                action="applied",
                detail=fix or str(key),
                brief_id=brief_id,
            )
        )
    for url in apply_summary.get("opened_prs") or []:
        rows.append(
            append_action(
                actor=actor,
                repo="-",
                action="opened_or_api",
                detail=str(url)[:200],
                pr_url=str(url) if str(url).startswith("http") else None,
                brief_id=brief_id,
            )
        )
    return rows


def sync_actions_to_controller(
    client: GitHubClient,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    ensure_runtime_dirs()
    local = DIST_DIR / ACTIONS_JSONL
    md = DIST_DIR / ACTIONS_MD
    out: dict[str, Any] = {"action": "skipped"}
    if not local.is_file():
        return out
    inbox = load_inbox()
    controller = _resolve_controller(client, inbox)
    if not controller or not inbox.get("enabled", True):
        return out
    if dry_run:
        out["action"] = "dry_run"
        return out
    try:
        day = datetime.now(UTC).strftime("%Y-%m-%d")
        out["jsonl_url"] = _put_file(
            client,
            controller,
            f"{REMOTE_DIR}/actions/{day}.jsonl",
            local.read_text(encoding="utf-8"),
            f"chore(argus): actions ledger {day}",
        )
        if md.is_file():
            out["md_url"] = _put_file(
                client,
                controller,
                f"{REMOTE_DIR}/{ACTIONS_MD}",
                md.read_text(encoding="utf-8"),
                f"chore(argus): actions changelog {day}",
            )
        out["action"] = "updated"
    except GitHubError as exc:
        out["action"] = "error"
        out["errors"] = [str(exc)]
    return out


def brief_ledger_dir(brief_id: str, *, dist_dir: Path | None = None) -> Path:
    base = (dist_dir or DIST_DIR) / "briefs" / brief_id
    base.mkdir(parents=True, exist_ok=True)
    return base


def write_brief_receipt(
    brief_id: str,
    payload: dict[str, Any],
    *,
    dist_dir: Path | None = None,
) -> Path:
    d = brief_ledger_dir(brief_id, dist_dir=dist_dir)
    path = d / "receipt.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
