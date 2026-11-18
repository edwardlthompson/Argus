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


def test_fleet_lists_every_active_repo_sorted_by_issues():
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
    names = [r["name"] for r in view["fleet"]]
    assert names == ["noisy", "mid", "healthy"]
    assert view["healthy_omitted"] == 0
    assert "bar_width" in view["fleet"][0]
    assert view["charts"]["fleet_attention"]["points"]


def test_fleet_sorts_issues_then_open_prs():
    low_i_high_pr = _plain("alpha", issues=1, attention=90.0)
    low_i_high_pr.repo.raw["open_prs_count"] = 20
    low_i_high_pr.repo.raw["open_issues_only"] = 1
    high_i = _plain("bravo", issues=5, attention=10.0)
    high_i.repo.raw["open_prs_count"] = 0
    high_i.repo.raw["open_issues_only"] = 5
    same_i_more_pr = _plain("charlie", issues=1, attention=5.0)
    same_i_more_pr.repo.raw["open_prs_count"] = 3
    same_i_more_pr.repo.raw["open_issues_only"] = 1
    view = build_report_view(
        [low_i_high_pr, high_i, same_i_more_pr],
        target_label="t",
        mode="run",
        pages_safe=True,
    )
    assert [r["name"] for r in view["fleet"]] == ["bravo", "alpha", "charlie"]


def test_gh_issues_excludes_prs_from_open_issues_count():
    from argus.report_view import _gh_open_issues, _gh_open_prs

    plan = _plain("runner", issues=14, attention=30.0)
    plan.repo.raw["open_issues_count"] = 14  # GitHub includes PRs
    plan.repo.raw["open_prs_count"] = 14
    plan.repo.raw["open_issues_only"] = 0
    assert _gh_open_issues(plan) == 0
    assert _gh_open_prs(plan) == 14
    # Still listed (PRs identified) but not as Issues.
    assert _needs_attention_listing(plan)
    view = build_report_view([plan], target_label="t", mode="run", pages_safe=True)
    row = view["fleet"][0]
    assert row["gh_issues"] == 0
    assert row["gh_prs"] == 14
    assert row["issues"] == 0
    assert row["prs"] == 14


def test_yolo_handlers_include_issue_ids():
    from argus.yolo import YOLO_AGENT_HANDLERS, YOLO_HANDLERS

    assert "ISSUE-PATTERNED-AUTO" in YOLO_HANDLERS
    assert "AGENT-STALE-ISSUES" in YOLO_AGENT_HANDLERS
