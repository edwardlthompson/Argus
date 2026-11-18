from __future__ import annotations

from argus.inbox_issues import (
    build_issue_body,
    build_issue_title,
    issue_marker,
    parse_marker,
    sync_inbox_issues,
)
from argus.models import (
    Confidence,
    Fix,
    FixClass,
    MatchedFix,
    RepoPlan,
    RepoRecord,
    RepoStatus,
    ScoreResult,
)
from argus.state import StateStore
from argus.status_page import compose_status_html, is_security_fix, safe_status_payload


def _human_fix(fid: str = "HYG-README", *, title: str = "Add README") -> Fix:
    return Fix(
        id=fid,
        class_=FixClass.HUMAN,
        title=title,
        why="Missing doc",
        applies_when="true",
        phase=1,
        depends_on=(),
        confidence=Confidence.HIGH,
        auto_safe=False,
        gate="README exists",
        agent_prompt=None,
        human_steps="1. Open the repo\n2. Add a README",
        resolution_ttl_days=30,
        profiles=("generic",),
    )


def _plan(repo: str, fixes: list[Fix]) -> RepoPlan:
    owner, name = repo.split("/", 1)
    return RepoPlan(
        repo=RepoRecord(
            full_name=repo,
            owner=owner,
            name=name,
            status=RepoStatus.ACTIVE,
            html_url=f"https://github.com/{repo}",
        ),
        score=ScoreResult(attention=10, confidence=Confidence.HIGH, category_scores={}),
        human_fixes=[MatchedFix(fix=f) for f in fixes],
    )


def test_marker_roundtrip():
    m = issue_marker("HYG-README", "acme/demo")
    assert "HYG-README" in m
    assert parse_marker(f"hello\n{m}\n") == ("HYG-README", "acme/demo")


def test_issue_body_contains_steps_and_marker():
    matched = MatchedFix(fix=_human_fix())
    body = build_issue_body(matched, "acme/demo")
    assert "<!-- argus:HYG-README:acme/demo -->" in body
    assert "Add a README" in body
    assert "Done when" in body
    assert "acme/demo/settings" in body
    title = build_issue_title(matched, "acme/demo")
    assert "acme/demo" in title


def test_security_fix_detection():
    assert is_security_fix("SEC-DEPENDABOT")
    assert not is_security_fix("HYG-README")


def test_status_page_has_counts_not_repo_names():
    plans = [_plan("acme/demo", [_human_fix()])]
    payload = safe_status_payload(plans)
    assert payload["human_open"] == 1
    assert payload["repo_count"] == 1
    html = compose_status_html(plans)
    assert "acme/demo" not in html
    assert "human tasks" in html
    assert "No security details" in html or "security details" in html.lower()


def test_sync_skips_security_when_disabled(tmp_path):
    store = StateStore(path=tmp_path / "t.sqlite")
    plans = [_plan("acme/demo", [_human_fix("SEC-SECRET-SCANNING", title="Enable secret scanning")])]
    result = sync_inbox_issues(
        client=None,  # type: ignore[arg-type]
        store=store,
        plans=plans,
        dry_run=True,
        config={
            "enabled": True,
            "controller_repo": "edwardlthompson/Argus",
            "security_issues": False,
            "max_issues_per_run": 5,
        },
    )
    assert result.skipped_security
    assert not any("SEC-" in x and not x.startswith("dry-run") for x in result.updated)
    # dry-run only lists non-security desired — security skipped before dry-run list
    assert result.updated == []
    store.close()


def test_sync_dry_run_lists_non_security(tmp_path):
    store = StateStore(path=tmp_path / "t.sqlite")
    plans = [_plan("acme/demo", [_human_fix()])]
    result = sync_inbox_issues(
        client=None,  # type: ignore[arg-type]
        store=store,
        plans=plans,
        dry_run=True,
        config={
            "enabled": True,
            "controller_repo": "edwardlthompson/Argus",
            "security_issues": False,
            "max_issues_per_run": 5,
        },
    )
    assert any("HYG-README" in x for x in result.updated)
    store.close()
