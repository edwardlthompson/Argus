"""Append-only notification history (safe fields when public)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from argus.paths import DATA_DIR, ensure_runtime_dirs

DEFAULT_CAP = 100


def append_notification_log(
    entry: dict[str, Any],
    *,
    path: Path | None = None,
    cap: int = DEFAULT_CAP,
) -> Path:
    ensure_runtime_dirs()
    out = path or (DATA_DIR / "notifications.json")
    rows: list[dict[str, Any]] = []
    if out.exists():
        try:
            raw = json.loads(out.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                rows = raw
        except json.JSONDecodeError:
            rows = []
    payload = {
        "ts": entry.get("ts") or datetime.now(UTC).isoformat(),
        "human_count": int(entry.get("human_count") or 0),
        "channels": list(entry.get("channels") or []),
        "run_url": entry.get("run_url"),
        "inbox_url": entry.get("inbox_url"),
        "skipped": entry.get("skipped"),
    }
    rows.append(payload)
    rows = rows[-cap:]
    out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return out
