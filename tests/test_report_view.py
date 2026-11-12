from __future__ import annotations

from argus.models import Confidence, RepoPlan, RepoRecord, RepoStatus, ScoreResult
from argus.report_view import (
    _band,
    _fix_prefix,
    _needs_attention_listing,
    _prefix_groups,
    build_report_view,
)


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


def _plain(name: str, *, issues: int, attention: float = 20.0) -> RepoPlan:
    return RepoPlan(
        repo=RepoRecord(
            full_name=f"acme/{name}",
            owner="acme",
            name=name,
            status=RepoStatus.ACTIVE,
            html_url=f"https://github.com/acme/{name}",
            raw={"language": "Python", "open_issues_count": issues},
        ),
        score=ScoreResult(
            attention=attention,
            confidence=Confidence.HIGH,
            category_scores={},
        ),
    )


def test_green_zero_issues_omitted_from_priority():
    healthy = _plain("healthy", issues=0, attention=50.0)
    noisy = _plain("noisy", issues=61, attention=12.0)
    mid = _plain("mid", issues=10, attention=40.0)
    assert not _needs_attention_listing(healthy)
    assert _needs_attention_listing(noisy)
    view = build_report_view(
        [healthy, noisy, mid],
        target_label="t",
        mode="run",
        pages_safe=True,
    )
    names = [c["name"] for c in view["priority_cards"]]
    assert "healthy" not in names
    assert names[0] == "noisy"  # most Issues first
    assert names[1] == "mid"
    assert view["healthy_omitted"] == 1
    assert view["fleet"] == []


def test_yolo_handlers_include_issue_ids():
    from argus.yolo import YOLO_AGENT_HANDLERS, YOLO_HANDLERS

    assert "ISSUE-PATTERNED-AUTO" in YOLO_HANDLERS
    assert "AGENT-STALE-ISSUES" in YOLO_AGENT_HANDLERS
