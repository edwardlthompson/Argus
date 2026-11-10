from __future__ import annotations

from pathlib import Path

from argus.cost import report
from argus.fleet import write_plan
from argus.fleet_exec import execute_plan, wave_batches
from argus.remote import argus_off, is_armed, load_remote


def test_wave_batches():
    caps = {"canary_size": 1, "batch_after_canary": 3, "batch_size": 5}
    waves = wave_batches([f"r{i}" for i in range(12)], caps)
    assert waves[0] == ["r0"]
    assert waves[1] == ["r1", "r2", "r3"]
    assert len(waves[2]) == 5


def test_execute_requires_verify(tmp_path: Path):
    write_plan("b1", ["o/a", "o/b"], verify="pytest", dist_dir=tmp_path)
    out = execute_plan("b1", approve=False, dist_dir=tmp_path, root=tmp_path)
    assert out["status"] == "dry_run"
    assert out["waves"]


def test_remote_off(tmp_path: Path):
    (tmp_path / "argus.remote.json").write_text(
        '{"enabled": true, "mode": "rw"}', encoding="utf-8"
    )
    assert is_armed(tmp_path)
    argus_off("test", root=tmp_path)
    assert (tmp_path / "ARGUS-OFF.md").is_file()
    assert (tmp_path / "YOLO-OFF.md").is_file()
    assert load_remote(tmp_path).get("enabled") is False
    assert not is_armed(tmp_path)


def test_cost_report():
    payload = report()
    assert "grok" in payload
    assert "argus_actions_logged" in payload
