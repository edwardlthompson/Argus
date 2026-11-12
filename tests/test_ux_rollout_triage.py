from __future__ import annotations

from pathlib import Path

from argus.models import (
    Confidence,
    Fix,
    FixClass,
    MatchedFix,
    RepoPlan,
    RepoRecord,
    ScoreResult,
)
from argus.triage import fleet_rollup, group_by_fix_class, summarize_triage
from argus.ux.rollout import (
    actionable,
    fp_rate,
    load_state,
    maybe_promote_demote,
    record_outcome,
    reportable,
    save_state,
    stage_for,
)
from argus.yolo import YOLO_AGENT_HANDLERS, is_yolo_deterministic_agent


def _fix(fid: str, cls: FixClass) -> Fix:
    return Fix(
        id=fid,
        class_=cls,
        title=fid,
        why="t",
        applies_when="True",
        phase=1,
        depends_on=(),
        confidence=Confidence.HIGH,
        auto_safe=cls == FixClass.AUTO_SAFE,
        gate="true",
        agent_prompt=None,
        human_steps=None,
        resolution_ttl_days=30,
        profiles=("generic",),
    )


def _plan(*matched: MatchedFix) -> RepoPlan:
    repo = RepoRecord(full_name="o/r", owner="o", name="r")
    plan = RepoPlan(
        repo=repo,
        score=ScoreResult(attention=10, confidence=Confidence.HIGH, category_scores={}),
        auto_fixes=[],
        agent_fixes=[],
        human_fixes=[],
    )
    for m in matched:
        if m.fix.class_ == FixClass.AUTO_SAFE:
            plan.auto_fixes.append(m)
        elif m.fix.class_ == FixClass.AGENT:
            plan.agent_fixes.append(m)
        else:
            plan.human_fixes.append(m)
    return plan


def test_rollout_promote_and_demote(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("argus.ux.rollout.STATE_DIR", tmp_path)
    monkeypatch.setattr("argus.ux.rollout.ensure_runtime_dirs", lambda: None)
    cfg = {
        "default_stage": "observe",
        "promote_fp_rate_max": 0.05,
        "demote_fp_rate_min": 0.20,
        "min_samples_for_promote": 3,
        "min_samples_for_demote": 3,
    }
    st = load_state(tmp_path / "ux_rollout.json")
    for _ in range(3):
        record_outcome("R1", false_positive=False, state=st, cfg=cfg, persist=False)
    assert stage_for("R1", state=st, cfg=cfg) == "soft"
    assert reportable("R1", state=st)
    assert not actionable("R1", state=st)
    for _ in range(3):
        record_outcome("R1", false_positive=False, state=st, cfg=cfg, persist=False)
    assert stage_for("R1", state=st, cfg=cfg) == "enforce"
    assert actionable("R1", state=st)
    # Force demote with high FP
    entry = st["rules"]["R1"]
    entry["false_positives"] = 10
    entry["true_positives"] = 1
    maybe_promote_demote("R1", state=st, cfg=cfg)
    assert stage_for("R1", state=st, cfg=cfg) == "soft"
    save_state(st, tmp_path / "ux_rollout.json")
    assert (tmp_path / "ux_rollout.json").is_file()
    assert fp_rate(entry) is not None


def test_triage_groups_by_class():
    plans = [
        _plan(
            MatchedFix(fix=_fix("A1", FixClass.AUTO_SAFE), reason="x"),
            MatchedFix(fix=_fix("G1", FixClass.AGENT), reason="x"),
            MatchedFix(fix=_fix("H1", FixClass.HUMAN), reason="x"),
        )
    ]
    groups = group_by_fix_class(plans)
    assert len(groups["auto_safe"]) == 1
    assert len(groups["agent"]) == 1
    assert len(groups["human"]) == 1
    s = summarize_triage(plans)
    assert s["counts"]["agent"] == 1
    f = fleet_rollup(plans)
    assert f["mode"] == "fleet"
    assert "H1" in f["by_fix_id"]


def test_yolo_agent_class_only():
    agent = MatchedFix(fix=_fix("AGENT-WHAT-NOT", FixClass.AGENT), reason="x")
    human = MatchedFix(fix=_fix("SEC-OPEN-DEPENDABOT-ALERTS", FixClass.HUMAN), reason="x")
    codeql = MatchedFix(fix=_fix("SEC-CODEQL", FixClass.AGENT), reason="x")
    assert is_yolo_deterministic_agent(agent)
    assert not is_yolo_deterministic_agent(human)
    assert is_yolo_deterministic_agent(codeql)
    assert "PR-STALE" in YOLO_AGENT_HANDLERS
    assert "SEC-CODEQL" in YOLO_AGENT_HANDLERS
