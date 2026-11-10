from __future__ import annotations

from pathlib import Path

from argus.grok_budget import (
    GrokCounters,
    check_allowed,
    load_counters,
    record_run,
    save_counters,
    trip_breaker,
)


def test_daily_cap_and_cooldown(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("argus.grok_budget.DIST_DIR", tmp_path)
    monkeypatch.setattr("argus.grok_budget.ensure_runtime_dirs", lambda: None)
    cfg = {
        "enabled": True,
        "max_runs_per_bot_per_day": 1,
        "max_total_bot_runs_per_day": 2,
        "max_estimated_tokens_per_day": 1000,
        "cooldown_hours": 20,
        "circuit_breaker": {"empty_or_error_trips": 3, "off_marker": "GROK-OFF.md"},
    }
    assert check_allowed("ci", cfg=cfg, root=tmp_path).allowed
    record_run("ci", tokens=10, cfg=cfg, root=tmp_path)
    assert check_allowed("ci", cfg=cfg, root=tmp_path).reason == "cooldown"


def test_token_cap_trips(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("argus.grok_budget.DIST_DIR", tmp_path)
    monkeypatch.setattr("argus.grok_budget.ensure_runtime_dirs", lambda: None)
    cfg = {
        "enabled": True,
        "max_runs_per_bot_per_day": 5,
        "max_total_bot_runs_per_day": 8,
        "max_estimated_tokens_per_day": 50,
        "cooldown_hours": 0,
        "circuit_breaker": {"empty_or_error_trips": 99, "off_marker": "GROK-OFF.md"},
    }
    c = GrokCounters(day=load_counters().day, tokens=40)
    save_counters(c)
    r = check_allowed("release", estimated_tokens=20, cfg=cfg, root=tmp_path)
    assert not r.allowed
    assert r.reason == "token_cap"


def test_breaker(tmp_path: Path):
    path = trip_breaker(
        "test",
        root=tmp_path,
        cfg={"circuit_breaker": {"off_marker": "GROK-OFF.md"}},
    )
    assert path.is_file()
    cfg = {"enabled": True, "circuit_breaker": {"off_marker": "GROK-OFF.md"}}
    assert not check_allowed("ci", cfg=cfg, root=tmp_path).allowed
