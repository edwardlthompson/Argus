from __future__ import annotations

from argus.health import (
    compare_snapshots,
    compose_delta_markdown,
    project_plans_after_apply,
    snapshot_plans,
)
from argus.models import (
    Confidence,
    Fix,
    FixClass,
    MatchedFix,
    RepoPlan,
    RepoRecord,
    ScoreResult,
)


def _plan(name: str, attention: float, auto_ids: list[str]) -> RepoPlan:
    owner, repo = name.split("/")
    fixes = [
        MatchedFix(
            fix=Fix(
                id=fid,
                class_=FixClass.AUTO_SAFE,
                title=fid,
                why="w",
                applies_when="True",
                phase=1,
                depends_on=(),
                confidence=Confidence.HIGH,
                auto_safe=True,
                gate="true",
                agent_prompt=None,
                human_steps=None,
                resolution_ttl_days=30,
                profiles=("generic",),
            )
        )
        for fid in auto_ids
    ]
    return RepoPlan(
        repo=RepoRecord(full_name=name, owner=owner, name=repo),
        score=ScoreResult(attention=attention, confidence=Confidence.HIGH, category_scores={}),
        auto_fixes=fixes,
    )


def test_snapshot_and_delta_projection():
    plans = [_plan("a/one", 40, ["HYGIENE-LICENSE"]), _plan("a/two", 10, [])]
    before = snapshot_plans(plans)
    assert before["totals"]["open_fixes"] == 1
    apply = {
        "applied": [],
        "would_prs": [{"repo": "a/one", "fix": "HYGIENE-LICENSE"}],
        "opened_prs": [],
    }
    project_plans_after_apply(plans, apply, dry_run=True)
    after = snapshot_plans(plans)
    delta = compare_snapshots(before, after, apply_summary=apply)
    assert after["totals"]["open_fixes"] == 0
    assert delta["delta_open_fixes"] == -1
    md = compose_delta_markdown(delta)
    assert "Open fixes" in md
    assert "a/one" in md
