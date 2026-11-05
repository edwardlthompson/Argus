"""Persistent portfolio state, resolution cache, and run history."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from argus.models import RepoStatus
from argus.paths import DATA_DIR, ensure_runtime_dirs


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class Resolution:
    repo: str
    fix_id: str
    resolved_at: str
    ttl_days: int
    source: str = "apply"

    def expired(self, now: datetime | None = None) -> bool:
        now = now or _utcnow()
        resolved = datetime.fromisoformat(self.resolved_at)
        return now > resolved + timedelta(days=self.ttl_days)


class StateStore:
    def __init__(self, path: Path | None = None) -> None:
        ensure_runtime_dirs()
        self.path = path or (DATA_DIR / "argus.sqlite")
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self._conn.close()

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS repos (
                full_name TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                seen_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                meta_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS resolutions (
                repo TEXT NOT NULL,
                fix_id TEXT NOT NULL,
                resolved_at TEXT NOT NULL,
                ttl_days INTEGER NOT NULL,
                source TEXT NOT NULL,
                PRIMARY KEY (repo, fix_id)
            );
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ran_at TEXT NOT NULL,
                mode TEXT NOT NULL,
                summary_json TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def upsert_repo(self, full_name: str, status: RepoStatus, meta: dict[str, Any] | None = None) -> None:
        self._conn.execute(
            """
            INSERT INTO repos(full_name, status, seen_at, active, meta_json)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(full_name) DO UPDATE SET
                status=excluded.status,
                seen_at=excluded.seen_at,
                active=1,
                meta_json=excluded.meta_json
            """,
            (full_name, status.value, _utcnow().isoformat(), json.dumps(meta or {})),
        )
        self._conn.commit()

    def set_status(self, full_name: str, status: RepoStatus) -> None:
        row = self._conn.execute(
            "SELECT meta_json FROM repos WHERE full_name=?", (full_name,)
        ).fetchone()
        meta = row["meta_json"] if row else "{}"
        self._conn.execute(
            """
            INSERT INTO repos(full_name, status, seen_at, active, meta_json)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(full_name) DO UPDATE SET status=excluded.status, seen_at=excluded.seen_at
            """,
            (full_name, status.value, _utcnow().isoformat(), meta),
        )
        self._conn.commit()

    def mark_inactive(self, full_name: str) -> None:
        self._conn.execute(
            "UPDATE repos SET active=0, seen_at=? WHERE full_name=?",
            (_utcnow().isoformat(), full_name),
        )
        self._conn.commit()

    def known_repos(self) -> dict[str, dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM repos").fetchall()
        out: dict[str, dict[str, Any]] = {}
        for row in rows:
            out[row["full_name"]] = {
                "status": RepoStatus(row["status"]),
                "active": bool(row["active"]),
                "seen_at": row["seen_at"],
                "meta": json.loads(row["meta_json"]),
            }
        return out

    def record_resolution(
        self, repo: str, fix_id: str, ttl_days: int = 30, source: str = "apply"
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO resolutions(repo, fix_id, resolved_at, ttl_days, source)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(repo, fix_id) DO UPDATE SET
                resolved_at=excluded.resolved_at,
                ttl_days=excluded.ttl_days,
                source=excluded.source
            """,
            (repo, fix_id, _utcnow().isoformat(), ttl_days, source),
        )
        self._conn.commit()

    def is_resolved(self, repo: str, fix_id: str) -> bool:
        row = self._conn.execute(
            "SELECT * FROM resolutions WHERE repo=? AND fix_id=?",
            (repo, fix_id),
        ).fetchone()
        if not row:
            return False
        res = Resolution(
            repo=row["repo"],
            fix_id=row["fix_id"],
            resolved_at=row["resolved_at"],
            ttl_days=row["ttl_days"],
            source=row["source"],
        )
        if res.expired():
            self._conn.execute(
                "DELETE FROM resolutions WHERE repo=? AND fix_id=?", (repo, fix_id)
            )
            self._conn.commit()
            return False
        return True

    def add_history(self, mode: str, summary: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO history(ran_at, mode, summary_json) VALUES (?, ?, ?)",
            (_utcnow().isoformat(), mode, json.dumps(summary)),
        )
        self._conn.commit()

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            {
                "id": r["id"],
                "ran_at": r["ran_at"],
                "mode": r["mode"],
                "summary": json.loads(r["summary_json"]),
            }
            for r in rows
        ]

    def export_snapshot(self) -> dict[str, Any]:
        return {
            "repos": {
                k: {**v, "status": v["status"].value} for k, v in self.known_repos().items()
            },
            "history": self.history(50),
        }

    def dump_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.export_snapshot(), indent=2), encoding="utf-8")


def sync_status_yaml(store: StateStore, declared: dict[str, RepoStatus]) -> None:
    """Apply declared status.yaml entries into the store."""
    for full_name, status in declared.items():
        store.set_status(full_name, status)
