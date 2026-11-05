"""Dry-run would_prs preview."""

from __future__ import annotations

from argus.apply import apply_auto_safe
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


class FakeClient:
    report_only = False


def test_dry_run_would_prs(tmp_path) -> None:
    fix = Fix(
        id="HYGIENE-GITIGNORE",
        class_=FixClass.AUTO_SAFE,
        title="gitignore",
        why="x",
        applies_when="True",
        phase=1,
        depends_on=(),
        confidence=Confidence.HIGH,
        auto_safe=True,
        gate="test -f .gitignore",
        agent_prompt=None,
        human_steps=None,
        resolution_ttl_days=30,
        profiles=("generic",),
    )
    repo = RepoRecord("o/r", "o", "r", status=RepoStatus.ACTIVE, permissions={"push": True})
    plan = RepoPlan(
        repo=repo,
        score=ScoreResult(0.0, Confidence.HIGH, {}, []),
        human_fixes=[],
        agent_fixes=[],
        auto_fixes=[MatchedFix(fix, "True")],
    )
    store = StateStore(path=tmp_path / "state.db")
    try:
        result = apply_auto_safe(FakeClient(), store, [plan], dry_run=True, max_prs=5)  # type: ignore[arg-type]
    finally:
        store.close()
    assert result.would_prs == [{"repo": "o/r", "fix": "HYGIENE-GITIGNORE", "path": ".gitignore"}]
