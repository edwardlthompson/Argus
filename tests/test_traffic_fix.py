from __future__ import annotations

from argus.config_loader import load_fixes
from argus.match import match_fixes
from argus.models import RepoRecord, RepoStatus
from argus.signals import fixture_bundle


def test_traffic_insights_unavailable_matches_when_api_denied():
    fixes = [f for f in load_fixes() if f.id == "TRAFFIC-INSIGHTS-UNAVAILABLE"]
    assert fixes
    repo = RepoRecord(
        full_name="alice/app",
        owner="alice",
        name="app",
        status=RepoStatus.ACTIVE,
        permissions={"push": True},
    )
    signals = fixture_bundle(
        {"traffic": {"traffic_ok": False, "views_14d": None, "clones_14d": None, "skipped": False}}
    )
    matched = match_fixes(fixes, repo, signals, store=None, profile="edward")
    assert [m.fix.id for m in matched] == ["TRAFFIC-INSIGHTS-UNAVAILABLE"]


def test_traffic_insights_skips_when_ok():
    fixes = [f for f in load_fixes() if f.id == "TRAFFIC-INSIGHTS-UNAVAILABLE"]
    repo = RepoRecord(
        full_name="alice/app",
        owner="alice",
        name="app",
        status=RepoStatus.ACTIVE,
        permissions={"push": True},
    )
    signals = fixture_bundle(
        {"traffic": {"traffic_ok": True, "views_14d": 9, "clones_14d": 1, "skipped": False}}
    )
    matched = match_fixes(fixes, repo, signals, store=None, profile="edward")
    assert matched == []
