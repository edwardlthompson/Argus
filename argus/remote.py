"""Remote control plane — product ships disabled + readonly."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from argus.paths import PROJECT_ROOT, STATE_DIR, ensure_runtime_dirs
from argus.yolo_arm import shutdown_yolo

REMOTE_NAME = "argus.remote.json"
OFF_MARKER = "ARGUS-OFF.md"


def remote_path(root: Path | None = None) -> Path:
    return (root or PROJECT_ROOT) / REMOTE_NAME


def load_remote(root: Path | None = None) -> dict[str, Any]:
    path = remote_path(root)
    if not path.is_file():
        return {"enabled": False, "mode": "readonly"}
    return json.loads(path.read_text(encoding="utf-8"))


def is_armed(root: Path | None = None) -> bool:
    cfg = load_remote(root)
    if (root or PROJECT_ROOT).joinpath(OFF_MARKER).is_file():
        return False
    return bool(cfg.get("enabled")) and str(cfg.get("mode") or "") != "readonly"


def append_remote_log(event: dict[str, Any], *, root: Path | None = None) -> Path:
    ensure_runtime_dirs()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "remote.log"
    row = {"ts": datetime.now(UTC).isoformat(), **event}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def argus_off(reason: str, *, root: Path | None = None) -> dict[str, Any]:
    """Disarm YOLO + remote; sticky ARGUS-OFF.md."""
    base = root or PROJECT_ROOT
    shutdown_yolo(reason, root=base)
    off = base / OFF_MARKER
    off.write_text(f"Argus off: {reason.strip()}\n", encoding="utf-8")
    cfg_path = remote_path(base)
    if cfg_path.is_file():
        cfg = load_remote(base)
        cfg["enabled"] = False
        cfg["mode"] = "readonly"
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    append_remote_log({"event": "argus_off", "reason": reason}, root=base)
    return {"off": str(off), "remote_enabled": False}
