"""Mode-aware Dependabot bump classification. Pure — no GitHub I/O."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

LEVELS = ("patch", "minor", "major")
_TRIPLE = re.compile(r"from\s+v?(\d+)\.(\d+)\.(\d+)\s+to\s+v?(\d+)\.(\d+)\.(\d+)", re.I)
_DOUBLE = re.compile(r"from\s+v?(\d+)\.(\d+)\s+to\s+v?(\d+)\.(\d+)\b", re.I)
_SINGLE = re.compile(r"from\s+v?(\d+)\s+to\s+v?(\d+)\b", re.I)

NORMAL_LEVELS = ("patch", "minor")
YOLO_LEVELS = ("patch", "minor", "major")


def is_dependabot_author(title: str, user_login: str | None = None) -> bool:
    login = (user_login or "").lower()
    return "dependabot" in login or "dependabot" in (title or "").lower()


def classify_dependabot_bump(title: str, user_login: str | None = None) -> str | None:
    """Return patch | minor | major | unknown, or None if not Dependabot."""
    if not is_dependabot_author(title, user_login):
        return None
    t = title or ""
    if re.search(r"\bmajor\b", t, re.I):
        return "major"
    triple = _TRIPLE.search(t)
    if triple:
        a = tuple(int(triple.group(i)) for i in range(1, 4))
        b = tuple(int(triple.group(i)) for i in range(4, 7))
        if b[0] > a[0]:
            return "major"
        if b[0] == a[0] and b[1] > a[1]:
            return "minor"
        return "patch"
    double = _DOUBLE.search(t)
    if double:
        a_maj, a_min = int(double.group(1)), int(double.group(2))
        b_maj, b_min = int(double.group(3)), int(double.group(4))
        if b_maj > a_maj:
            return "major"
        if b_maj == a_maj and b_min > a_min:
            return "minor"
        return "patch"
    single = _SINGLE.search(t)
    if single:
        old, new = int(single.group(1)), int(single.group(2))
        if new > old:
            return "major"
        return "patch"
    if re.search(r"\bminor\b", t, re.I):
        return "minor"
    if re.search(r"\bpatch\b", t, re.I):
        return "patch"
    return "unknown"


def normalize_levels(raw: Any, default: Iterable[str]) -> list[str]:
    fallback = [x for x in default if x in LEVELS]
    if not raw:
        return list(fallback)
    out: list[str] = []
    for item in raw:
        key = str(item).strip().lower()
        if key in LEVELS and key not in out:
            out.append(key)
    return out or list(fallback)


def bump_allowed(level: str | None, allowed: Iterable[str]) -> bool:
    if level is None:
        return False
    allowed_set = {str(x).lower() for x in allowed}
    if allowed_set >= set(LEVELS):
        return True
    if level == "unknown":
        return False
    return level in allowed_set


def merge_enabled(safety: dict[str, Any] | None, *, yolo: bool) -> bool:
    safety = safety or {}
    if yolo:
        block = safety.get("yolo") or {}
        if "auto_merge_dependabot" in block:
            return bool(block["auto_merge_dependabot"])
        return bool(block.get("auto_merge_dependabot_patch", True))
    block = safety.get("normal") or {}
    if "merge_dependabot" in block:
        return bool(block["merge_dependabot"])
    return bool(block.get("merge_dependabot_patch", True))


def allowed_levels(safety: dict[str, Any] | None, *, yolo: bool) -> list[str]:
    safety = safety or {}
    block = (safety.get("yolo") if yolo else safety.get("normal")) or {}
    default = YOLO_LEVELS if yolo else NORMAL_LEVELS
    return normalize_levels(block.get("dependabot_auto_merge_levels"), default)
