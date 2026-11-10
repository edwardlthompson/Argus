"""Dual-plane YOLO arming: product off; private runner armed via yolo.on."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from argus.paths import ROOT


def yolo_on_path(root: Path | None = None) -> Path:
    return (root or ROOT) / "yolo.on"


def yolo_off_marker(root: Path | None = None) -> Path:
    return (root or ROOT) / "YOLO-OFF.md"


def is_yolo_armed(safety: dict[str, Any] | None = None, *, root: Path | None = None) -> bool:
    """True when private-runner YOLO should run.

    Armed if `yolo.on` exists (preferred) or apply_mode is yolo (runner legacy).
    Disarmed if YOLO-OFF.md sticky marker exists (overrides file/mode).
    RULES-STALE blocks YOLO even when armed.
    """
    base = root or ROOT
    if yolo_off_marker(base).is_file():
        return False
    try:
        from argus.rules_sync import block_mutations

        if block_mutations(base):
            return False
    except Exception:  # noqa: BLE001
        pass
    if yolo_on_path(base).is_file():
        return True
    mode = str((safety or {}).get("apply_mode") or "normal")
    return mode == "yolo"


def shutdown_yolo(reason: str, *, root: Path | None = None) -> Path:
    """Sticky kill: remove yolo.on and write YOLO-OFF.md."""
    base = root or ROOT
    on = yolo_on_path(base)
    if on.is_file():
        on.unlink()
    off = yolo_off_marker(base)
    off.write_text(f"YOLO off: {reason.strip()}\n", encoding="utf-8")
    return off
