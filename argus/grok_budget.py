"""Daily Grok Bot run/token caps + circuit breaker."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from argus.paths import CONFIG_DIR, DIST_DIR, PROJECT_ROOT, ensure_runtime_dirs


@dataclass
class GrokBudgetResult:
    allowed: bool
    reason: str = ""
    remaining_runs: int = 0
    remaining_tokens: int = 0
    breaker_open: bool = False


@dataclass
class GrokCounters:
    day: str = ""
    runs: int = 0
    tokens: int = 0
    by_bot: dict[str, list[str]] = field(default_factory=dict)
    errors: int = 0


def load_grok_config(path: Path | None = None) -> dict[str, Any]:
    p = path or (CONFIG_DIR / "grok_bots.yaml")
    if not p.is_file():
        return {"enabled": False}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _counter_path() -> Path:
    ensure_runtime_dirs()
    return DIST_DIR / "grok-budget.json"


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def load_counters() -> GrokCounters:
    path = _counter_path()
    day = _today()
    if not path.is_file():
        return GrokCounters(day=day)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return GrokCounters(day=day)
    if raw.get("day") != day:
        return GrokCounters(day=day)
    return GrokCounters(
        day=day,
        runs=int(raw.get("runs") or 0),
        tokens=int(raw.get("tokens") or 0),
        by_bot=dict(raw.get("by_bot") or {}),
        errors=int(raw.get("errors") or 0),
    )


def save_counters(c: GrokCounters) -> None:
    _counter_path().write_text(
        json.dumps({
            "day": c.day,
            "runs": c.runs,
            "tokens": c.tokens,
            "by_bot": c.by_bot,
            "errors": c.errors,
        }, indent=2)
        + "\n",
        encoding="utf-8",
    )


def breaker_open(cfg: dict[str, Any] | None = None, *, root: Path | None = None) -> bool:
    cfg = cfg or load_grok_config()
    marker = str((cfg.get("circuit_breaker") or {}).get("off_marker") or "GROK-OFF.md")
    return (root or PROJECT_ROOT).joinpath(marker).is_file()


def trip_breaker(reason: str, *, root: Path | None = None, cfg: dict[str, Any] | None = None) -> Path:
    cfg = cfg or load_grok_config()
    marker = str((cfg.get("circuit_breaker") or {}).get("off_marker") or "GROK-OFF.md")
    path = (root or PROJECT_ROOT) / marker
    path.write_text(f"GROK off: {reason.strip()}\n", encoding="utf-8")
    return path


def check_allowed(
    bot_id: str,
    *,
    estimated_tokens: int = 0,
    cfg: dict[str, Any] | None = None,
    root: Path | None = None,
) -> GrokBudgetResult:
    cfg = cfg or load_grok_config()
    if not cfg.get("enabled", True):
        return GrokBudgetResult(False, "disabled")
    if breaker_open(cfg, root=root):
        return GrokBudgetResult(False, "breaker_open", breaker_open=True)
    c = load_counters()
    max_total = int(cfg.get("max_total_bot_runs_per_day") or 8)
    max_bot = int(cfg.get("max_runs_per_bot_per_day") or 2)
    max_tok = int(cfg.get("max_estimated_tokens_per_day") or 50_000)
    cooldown_h = float(cfg.get("cooldown_hours") or 20)
    bot_runs = list(c.by_bot.get(bot_id) or [])
    if bot_runs:
        try:
            last = datetime.fromisoformat(bot_runs[-1])
            if datetime.now(UTC) - last < timedelta(hours=cooldown_h):
                return GrokBudgetResult(False, "cooldown")
        except ValueError:
            pass
    if len(bot_runs) >= max_bot:
        return GrokBudgetResult(False, "bot_daily_cap")
    if c.runs >= max_total:
        return GrokBudgetResult(False, "total_daily_cap")
    if c.tokens + estimated_tokens > max_tok:
        return GrokBudgetResult(False, "token_cap")
    return GrokBudgetResult(
        True,
        "ok",
        remaining_runs=max_total - c.runs,
        remaining_tokens=max_tok - c.tokens,
    )


def record_run(
    bot_id: str,
    *,
    tokens: int = 0,
    error: bool = False,
    cfg: dict[str, Any] | None = None,
    root: Path | None = None,
) -> GrokBudgetResult:
    cfg = cfg or load_grok_config()
    c = load_counters()
    c.runs += 1
    c.tokens += max(0, tokens)
    c.by_bot.setdefault(bot_id, []).append(datetime.now(UTC).isoformat())
    if error:
        c.errors += 1
    save_counters(c)
    trips = int((cfg.get("circuit_breaker") or {}).get("empty_or_error_trips") or 3)
    if c.errors >= trips:
        trip_breaker(f"{c.errors} error digests in day", root=root, cfg=cfg)
        return GrokBudgetResult(False, "breaker_tripped", breaker_open=True)
    return check_allowed(bot_id, cfg=cfg, root=root)
