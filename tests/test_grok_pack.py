"""Unit: Tuesday Steward bootstrap pack."""

from __future__ import annotations

from pathlib import Path

from argus.grok_pack import pack_tuesday_steward


def test_pack_tuesday_steward_writes_bootstrap(tmp_path, monkeypatch):
    monkeypatch.setattr("argus.grok_pack.DIST_DIR", tmp_path)
    monkeypatch.setattr("argus.grok_pack.ensure_runtime_dirs", lambda: None)
    out = pack_tuesday_steward(allowlist=["edwardlthompson/Argus"])
    path = Path(out["bootstrap"])
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Tuesday Steward" in text
    assert "edwardlthompson/Argus" in text
    assert "health-infographic" in text
