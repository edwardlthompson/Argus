"""Sanitized Pages dashboard + pages_safe report view."""

from __future__ import annotations

from argus.models import (
    Confidence,
    Fix,
    FixClass,
    MatchedFix,
    RepoPlan,
    RepoRecord,
    ScoreResult,
)
from argus.portfolio_pages import write_portfolio_pages
from argus.report_view import _fix_prefix, build_report_view
from argus.steward_brief import write_steward_brief


def _fix(fid: str) -> Fix:
    return Fix(
        id=fid,
        class_=FixClass.HUMAN,
        title=f"Secret title for {fid}",
        why="why",
        applies_when="True",
        phase=1,
        depends_on=(),
        confidence=Confidence.HIGH,
        auto_safe=False,
        gate="done",
        agent_prompt=None,
        human_steps="do the thing",
        resolution_ttl_days=30,
        profiles=("generic",),
    )


def _plan(name: str, *, attention: float = 40.0, fix_id: str = "SEC-CODEQL") -> RepoPlan:
    return RepoPlan(
        repo=RepoRecord(
            full_name=f"acme/{name}",
            owner="acme",
            name=name,
            html_url=f"https://github.com/acme/{name}",
            description="demo",
            raw={"language": "Python", "stargazers_count": 1, "open_issues_count": 2},
        ),
        score=ScoreResult(
            attention=attention,
            confidence=Confidence.HIGH,
            category_scores={"security": 40.0, "hygiene": 10.0},
        ),
        human_fixes=[MatchedFix(fix=_fix(fix_id))],
    )


def test_fix_prefix_buckets():
    assert _fix_prefix("SEC-CODEQL") == "SEC"
    assert _fix_prefix("HYGIENE-LICENSE") == "HYGIENE"
    assert _fix_prefix("weird") == "OTHER"


def test_pages_safe_omits_issue_titles_and_grandma():
    plans = [_plan("one"), _plan("two", attention=70.0, fix_id="HYGIENE-LICENSE")]
    safe = build_report_view(plans, target_label="t", mode="run", pages_safe=True)
    full = build_report_view(plans, target_label="t", mode="run", pages_safe=False)
    assert safe["pages_safe"] is True
    assert len(safe["fleet"]) == 2
    assert safe["grandma_tasks"] == []
    assert "Secret title" not in str(safe)
    assert full["grandma_tasks"]
    assert any(r["key"] == "SEC" for r in safe["charts"]["prefix_groups"])
    assert safe["charts"]["rubric_means"]
    assert "bar_width" in safe["fleet"][0]


def test_write_portfolio_pages_and_steward(tmp_path):
    plans = [_plan("alpha")]
    pages = write_portfolio_pages(
        plans, dist_dir=tmp_path, health_delta={"delta_open_fixes": -1}
    )
    html = pages["portfolio_pages"].read_text(encoding="utf-8")
    assert "Argus" in html
    assert "Secret title" not in html
    assert pages["portfolio_pages_json"].is_file()
    steward = write_steward_brief(
        plans,
        dist_dir=tmp_path,
        hotspots={"by_fix_id": [{"id": "SEC-CODEQL", "count": 2}]},
    )
    text = steward.read_text(encoding="utf-8")
    assert "Tuesday Steward" in text
    assert "Private" in text
    assert "SEC-CODEQL" in text


def test_operational_dashboard_kpis_gauges_and_target_first(tmp_path):
    red = _plan("broken-ci", attention=10.0, fix_id="CI-LATEST-FAILED")
    red.repo.raw.update(
        {
            "open_issues_only": 1,
            "open_prs_count": 3,
            "pr_dependabot": 2,
            "pr_release": 1,
            "pr_feature": 0,
            "ci_has_workflows": True,
            "ci_latest_conclusion": "failure",
            "ci_latest_failed": True,
            "pushed_at": "2026-11-22T10:00:00Z",
        }
    )
    clean = RepoPlan(
        repo=RepoRecord(
            full_name="acme/clean-repo",
            owner="acme",
            name="clean-repo",
            html_url="https://github.com/acme/clean-repo",
            raw={
                "language": "Python",
                "open_issues_only": 0,
                "open_prs_count": 0,
                "ci_has_workflows": True,
                "ci_latest_conclusion": "success",
                "ci_latest_failed": False,
                "pushed_at": "2026-11-22T09:00:00Z",
            },
        ),
        score=ScoreResult(attention=5.0, confidence=Confidence.HIGH, category_scores={}),
    )
    view = build_report_view([clean, red], target_label="acme", mode="report", pages_safe=True)
    stats = view["stats"]
    assert stats["open_issues"] == 1
    assert stats["open_prs"] == 3
    assert stats["pr_dependabot"] == 2
    assert stats["pr_release"] == 1
    assert stats["pr_feature"] == 0
    assert stats["ci_passing"] == 1
    assert stats["ci_failing"] == 1
    assert stats["ci_pass_pct"] == 50.0
    assert stats["hygiene_clean"] == 1
    assert stats["zero_backlog"] == 1
    assert len(view["charts"]["health_gauges"]) == 3
    assert view["charts"]["backlog_top8"][0]["name"] == "broken-ci"
    assert view["target_first"][0]["name"] == "broken-ci"
    assert "Secret title" not in str(view)

    pages = write_portfolio_pages([clean, red], dist_dir=tmp_path)
    html = pages["portfolio_pages"].read_text(encoding="utf-8")
    assert "Portfolio Health Scorecard" in html
    assert "Fix These First" in html
    assert "Open Issues" in html
    assert "Open PRs" in html
    assert "CI Health" in html
    assert "Mean attention" not in html
    assert "Secret title" not in html
