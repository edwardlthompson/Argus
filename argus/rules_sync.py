"""Parent rule sync: live | pinned | vendored + RULES-STALE gate."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from argus.paths import PROJECT_ROOT

UPSTREAM_NAME = "argus.upstream.json"
LOCK_NAME = "argus.rules.lock"
CACHE_DIR = PROJECT_ROOT / ".argus" / "cache" / "rules"


def upstream_path(root: Path | None = None) -> Path:
    return (root or PROJECT_ROOT) / UPSTREAM_NAME


def lock_path(root: Path | None = None) -> Path:
    return (root or PROJECT_ROOT) / LOCK_NAME


def load_upstream(root: Path | None = None) -> dict[str, Any]:
    path = upstream_path(root)
    if not path.is_file():
        return {"mode": "vendored", "parent": "", "ref": "", "rules_paths": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_lock(root: Path | None = None) -> dict[str, Any]:
    path = lock_path(root)
    if not path.is_file():
        return {
            "version": 1,
            "tree_sha256": None,
            "synced_at": None,
            "pending_rules": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_lock(data: dict[str, Any], root: Path | None = None) -> Path:
    path = lock_path(root)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def tree_sha256(paths: list[str], *, root: Path | None = None) -> str:
    base = root or PROJECT_ROOT
    h = hashlib.sha256()
    files: list[Path] = []
    for rel in paths:
        p = base / rel
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(x for x in p.rglob("*") if x.is_file()))
    for f in sorted(files, key=lambda x: x.as_posix()):
        h.update(f.relative_to(base).as_posix().encode())
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def compute_local_tree(root: Path | None = None) -> str:
    up = load_upstream(root)
    paths = list(up.get("rules_paths") or ["config/fixes"])
    return tree_sha256(paths, root=root)


def rules_stale(root: Path | None = None) -> bool:
    lock = load_lock(root)
    expected = lock.get("tree_sha256")
    if not expected:
        return False  # never synced — not stale yet
    return compute_local_tree(root) != expected


def block_mutations(root: Path | None = None) -> bool:
    """True when YOLO/fanout/remote must not mutate (RULES-STALE)."""
    return rules_stale(root)


def sync_lock(
    *,
    root: Path | None = None,
    pending: list[str] | None = None,
) -> dict[str, Any]:
    """Record current tree hash as synced (operator pin after review)."""
    up = load_upstream(root)
    digest = compute_local_tree(root)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    marker = CACHE_DIR / "last_sync.json"
    payload = {
        "version": 1,
        "tree_sha256": digest,
        "synced_at": datetime.now(UTC).isoformat(),
        "parent": up.get("parent"),
        "ref": up.get("ref"),
        "mode": up.get("mode"),
        "pending_rules": list(pending or []),
    }
    save_lock(payload, root)
    marker.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def diff_lock(root: Path | None = None) -> dict[str, Any]:
    lock = load_lock(root)
    current = compute_local_tree(root)
    return {
        "locked": lock.get("tree_sha256"),
        "current": current,
        "stale": bool(lock.get("tree_sha256") and lock.get("tree_sha256") != current),
        "pending_rules": list(lock.get("pending_rules") or []),
        "mode": load_upstream(root).get("mode"),
        "ref": load_upstream(root).get("ref"),
    }


def bump_ref(new_ref: str, *, root: Path | None = None) -> dict[str, Any]:
    path = upstream_path(root)
    data = load_upstream(root)
    data["ref"] = new_ref
    data["mode"] = "pinned"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def status_payload(root: Path | None = None) -> dict[str, Any]:
    d = diff_lock(root)
    return {
        **d,
        "RULES-STALE": d["stale"],
        "block_yolo_fanout_remote": d["stale"],
    }
