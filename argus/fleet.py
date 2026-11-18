"""Fleet plan / halt / revert spine (upgrade-wave rails)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from argus.action_ledger import (
    ACTIONS_JSONL,
    append_action,
    brief_ledger_dir,
    write_brief_receipt,
)
from argus.paths import CONFIG_DIR, DIST_DIR, PROJECT_ROOT, ensure_runtime_dirs


def load_fleet_config(path: Path | None = None) -> dict[str, Any]:
    p = path or (CONFIG_DIR / "fleet.json")
    if not p.is_file():
        return {"enabled": False, "caps": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def halt_marker(root: Path | None = None) -> Path:
    return (root or PROJECT_ROOT) / "FLEET-HALT.md"


def is_halted(root: Path | None = None) -> bool:
    return halt_marker(root).is_file()


def halt(reason: str, *, root: Path | None = None) -> Path:
    path = halt_marker(root)
    path.write_text(f"Fleet halted: {reason.strip()}\n", encoding="utf-8")
    return path


def clear_halt(*, root: Path | None = None) -> bool:
    path = halt_marker(root)
    if path.is_file():
        path.unlink()
        return True
    return False


def write_plan(
    brief_id: str,
    repos: list[str],
    *,
    verify: str,
    auto: bool = False,
    dist_dir: Path | None = None,
) -> Path:
    if not (verify or "").strip():
        raise ValueError("fleet plan requires verify:")
    d = brief_ledger_dir(brief_id, dist_dir=dist_dir)
    payload = {
        "brief_id": brief_id,
        "repos": list(repos),
        "verify": verify.strip(),
        "auto": bool(auto),
        "created": datetime.now(UTC).isoformat(),
        "status": "planned",
    }
    path = d / "plan.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_brief_receipt(brief_id, {"kind": "plan", **payload}, dist_dir=dist_dir)
    return path


def load_actions(dist_dir: Path | None = None) -> list[dict[str, Any]]:
    path = (dist_dir or DIST_DIR) / ACTIONS_JSONL
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def revert_brief(
    brief_id: str,
    *,
    dist_dir: Path | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    ensure_runtime_dirs()
    rows = [r for r in load_actions(dist_dir) if r.get("brief_id") == brief_id]
    rows.reverse()
    receipt = {
        "brief_id": brief_id,
        "dry_run": dry_run,
        "ts": datetime.now(UTC).isoformat(),
        "steps": [
            {
                "repo": r.get("repo"),
                "action": r.get("action"),
                "sha_before": r.get("sha_before"),
                "sha_after": r.get("sha_after"),
                "pr_url": r.get("pr_url"),
                "undo": "revert_to_sha_before" if r.get("sha_before") else "manual",
            }
            for r in rows
        ],
    }
    path = write_brief_receipt(
        brief_id, {"kind": "revert", **receipt}, dist_dir=dist_dir
    )
    if not dry_run:
        append_action(
            actor="fleet",
            repo="-",
            action="revert_receipt",
            detail=brief_id,
            brief_id=brief_id,
            dist_dir=dist_dir,
        )
    receipt["receipt_path"] = str(path)
    return receipt
