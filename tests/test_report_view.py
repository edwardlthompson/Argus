from __future__ import annotations

from argus.report_view import _band


def test_band_empty_fixes_always_good():
    assert _band(80, open_any=False) == "good"
    assert _band(40, open_any=False) == "good"
    assert _band(10, open_any=False) == "good"


def test_band_with_open_fixes_uses_thresholds():
    assert _band(60, open_any=True) == "high"
    assert _band(40, open_any=True) == "medium"
    assert _band(20, open_any=True) == "good"
