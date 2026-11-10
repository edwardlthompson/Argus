from __future__ import annotations

from argus.fleet_apply import EXCLUDE, expected_version
from argus.fleet_exec import wave_batches


def test_exclude_hard_floors():
    assert "edwardlthompson/Argus" in EXCLUDE
    assert "edwardlthompson/argus-runner" in EXCLUDE
    assert "edwardlthompson/agent-project-bootstrap" in EXCLUDE


def test_expected_version_pinned():
    assert expected_version() == "1.13.0"


def test_wave_canary_first():
    waves = wave_batches(
        ["a/r1", "a/r2", "a/r3", "a/r4"],
        {"canary_size": 1, "batch_after_canary": 3, "batch_size": 5},
    )
    assert waves[0] == ["a/r1"]
