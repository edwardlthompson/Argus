"""Append-only apply/change history — local dist + private controller repo."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from argus.config_loader import load_inbox
from argus.github_client import GitHubClient, GitHubError
from argus.paths import DIST_DIR, ensure_runtime_dirs

HISTORY_JSONL = "apply-history.jsonl"
HISTORY_MD = "APPLY_HISTORY.md"
REMOTE_DIR = "argus-history"


@dataclass
class ApplyHistoryResult:
    local_jsonl: str = ""
    local_md: str = ""
    remote_url: str | None = None
    action: str = "skipped"
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def _entry(
    *,
    apply_summary: dict[str, Any],
    health: dict[str, Any] | None,
    dry_run: bool,
    skip_profile: bool,
    mode: str,
) -> dict[str, Any]:
    return {
        "ts": datetime.now(UTC).isoformat(),
        "mode": mode,
        "dry_run": dry_run,
        "skip_profile": skip_profile,
        "applied": list(apply_summary.get("applied") or []),
        "opened_prs": list(apply_summary.get("opened_prs") or []),
        "would_prs": list(apply_summary.get("would_prs") or []),
        "errors": list(apply_summary.get("errors") or [])[:50],
        "health": health or {},
    }


def append_local_history(entry: dict[str, Any], *, dist_dir: Path | None = None) -> tuple[Path, Path]:
    ensure_runtime_dirs()
    out = dist_dir or DIST_DIR
    out.mkdir(parents=True, exist_ok=True)
    jsonl = out / HISTORY_JSONL
    with jsonl.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    md = out / HISTORY_MD
    lines = [
        f"## {entry.get('ts')} — {entry.get('mode')} "
        f"({'dry-run' if entry.get('dry_run') else 'apply'})",
        "",
    ]
    applied = entry.get("applied") or []
    opened = entry.get("opened_prs") or []
    would = entry.get("would_prs") or []
    if applied:
        lines.append("### Applied")
        lines.extend(f"- `{x}`" for x in applied)
        lines.append("")
    if opened:
        lines.append("### PRs / API results")
        lines.extend(f"- {x}" for x in opened)
        lines.append("")
    if would and not applied:
        lines.append("### Would apply")
        for w in would:
            lines.append(f"- `{w.get('repo')}` / `{w.get('fix')}`")
        lines.append("")
    health = entry.get("health") or {}
    if health:
        lines.append(
            f"_Health open fixes: {health.get('before', {}).get('open_fixes')} → "
            f"{health.get('after', {}).get('open_fixes')}_"
        )
        lines.append("")
    lines.append("---")
    lines.append("")
    prev = md.read_text(encoding="utf-8") if md.exists() else (
        "# Argus apply history\n\n"
        "Append-only log of auto_safe / API changes. Private runner keeps the "
        f"canonical copy under `{REMOTE_DIR}/`.\n\n"
    )
    md.write_text(prev + "\n".join(lines), encoding="utf-8")
    return jsonl, md


def _resolve_controller(client: GitHubClient, inbox: dict[str, Any]) -> str | None:
    raw = str(inbox.get("controller_repo") or "").strip()
    if not raw or raw.lower().endswith("/argus"):
        return None
    if "YOUR_LOGIN" in raw:
        try:
            login = str((client.whoami() or {}).get("login") or "")
        except GitHubError:
            return None
        if not login:
            return None
        raw = raw.replace("YOUR_LOGIN", login)
    if raw.count("/") != 1:
        return None
    return raw


def _put_file(
    client: GitHubClient,
    full_name: str,
    path: str,
    content: str,
    message: str,
) -> str:
    owner, name = full_name.split("/", 1)
    repo = client.get(f"/repos/{owner}/{name}")
    if not repo.get("private", True) and "argus-runner" not in full_name.lower():
        # Never write change history onto a public product repo.
        raise GitHubError(f"Refusing apply-history write to non-private {full_name}")
    default = str(repo.get("default_branch") or "main")
    sha = None
    try:
        existing = client.get(
            f"/repos/{owner}/{name}/contents/{path}", params={"ref": default}
        )
        if isinstance(existing, dict):
            sha = existing.get("sha")
    except GitHubError:
        sha = None
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload: dict[str, Any] = {
        "message": message,
        "content": encoded,
        "branch": default,
    }
    if sha:
        payload["sha"] = sha
    client.put(
        f"/repos/{owner}/{name}/contents/{path}",
        allow_write=True,
        json=payload,
    )
    return f"https://github.com/{full_name}/blob/{default}/{path}"


def sync_history_to_controller(
    client: GitHubClient,
    *,
    local_jsonl: Path,
    local_md: Path,
    dry_run: bool = False,
) -> ApplyHistoryResult:
    result = ApplyHistoryResult(
        local_jsonl=str(local_jsonl),
        local_md=str(local_md),
    )
    inbox = load_inbox()
    if not inbox.get("enabled", True):
        result.detail = "inbox_disabled"
        return result
    controller = _resolve_controller(client, inbox)
    if not controller:
        result.detail = "no_controller"
        return result
    if dry_run:
        result.action = "dry_run"
        result.detail = f"would_update:{controller}/{REMOTE_DIR}/"
        return result
    try:
        md_url = _put_file(
            client,
            controller,
            f"{REMOTE_DIR}/{HISTORY_MD}",
            local_md.read_text(encoding="utf-8"),
            "chore(argus): update apply history markdown",
        )
        jsonl_url = _put_file(
            client,
            controller,
            f"{REMOTE_DIR}/{HISTORY_JSONL}",
            local_jsonl.read_text(encoding="utf-8"),
            "chore(argus): update apply history jsonl",
        )
        result.action = "updated"
        result.remote_url = md_url
        result.detail = jsonl_url
    except GitHubError as exc:
        result.action = "error"
        result.errors.append(str(exc))
    return result


def record_apply_history(
    client: GitHubClient,
    *,
    apply_summary: dict[str, Any],
    health: dict[str, Any] | None,
    dry_run: bool,
    skip_profile: bool,
    mode: str,
    sync_remote: bool = True,
) -> ApplyHistoryResult:
    """Always append locally; sync to private controller when not dry-run."""
    # Skip empty dry-runs with nothing to say
    if dry_run and not (apply_summary.get("would_prs") or apply_summary.get("applied")):
        if not apply_summary.get("attempted"):
            return ApplyHistoryResult(action="skipped", detail="empty")
    entry = _entry(
        apply_summary=apply_summary,
        health=health,
        dry_run=dry_run,
        skip_profile=skip_profile,
        mode=mode,
    )
    jsonl, md = append_local_history(entry)
    result = ApplyHistoryResult(local_jsonl=str(jsonl), local_md=str(md), action="local")
    if not sync_remote:
        result.detail = "local_only"
        return result
    remote = sync_history_to_controller(
        client, local_jsonl=jsonl, local_md=md, dry_run=dry_run
    )
    result.action = remote.action if remote.action != "skipped" else "local"
    result.remote_url = remote.remote_url
    result.detail = remote.detail or result.detail
    result.errors.extend(remote.errors)
    return result
