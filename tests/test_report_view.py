from __future__ import annotations

from argus.report_view import _band, _fix_prefix, _prefix_groups


def test_band_empty_fixes_always_good():
    assert _band(80, open_any=False) == "good"
    assert _band(40, open_any=False) == "good"
    assert _band(10, open_any=False) == "good"


def test_band_with_open_fixes_uses_thresholds():
    assert _band(60, open_any=True) == "high"
    assert _band(40, open_any=True) == "medium"
    assert _band(20, open_any=True) == "good"


def test_prefix_groups_aggregate():
    assert _fix_prefix("LINEAGE-VERSION-STALE") == "LINEAGE"
    rows = _prefix_groups({"SEC-A": 2, "SEC-B": 1, "CI-LATEST-FAILED": 4})
    by_key = {r["key"]: r["count"] for r in rows}
    assert by_key["SEC"] == 3
    assert by_key["CI"] == 4
