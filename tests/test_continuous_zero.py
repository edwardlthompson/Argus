"""Continuous zero: signal scope, API handlers, CI soft-resolve."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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
from argus.signals.contract import _controller_repo_names, is_controller_repo
from argus.state import StateStore
from argus.yolo import (
    YOLO_API_SAFE_HANDLERS,
    apply_yolo_extras,
    is_yolo_deterministic_agent,
)


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
        auto_safe=False,
        gate="true",
        agent_prompt="do it" if cls == FixClass.AGENT else None,
        human_steps="steps" if cls == FixClass.HUMAN else None,
        resolution_ttl_days=30,
        profiles=("generic",),
    )


def _plan(name: str, *matched: MatchedFix, push: bool = True) -> RepoPlan:
    owner, _, repo = name.partition("/")
    rec = RepoRecord(
        full_name=name,
        owner=owner or "o",
        name=repo or name,
        status=RepoStatus.ACTIVE,
        permissions={"push": push},
    )
    plan = RepoPlan(
        repo=rec,
        score=ScoreResult(attention=1, confidence=Confidence.HIGH, category_scores={}),
    )
    for m in matched:
        if m.fix.class_ == FixClass.HUMAN:
            plan.human_fixes.append(m)
        elif m.fix.class_ == FixClass.AGENT:
            plan.agent_fixes.append(m)
        else:
            plan.auto_fixes.append(m)
    return plan


def test_controller_names_include_argus():
    names = _controller_repo_names()
    assert "argus" in names
    assert is_controller_repo(RepoRecord("edwardlthompson/Argus", "edwardlthompson", "Argus"))
    assert not is_controller_repo(RepoRecord("edwardlthompson/other", "edwardlthompson", "other"))


def test_contract_no_rules_stale_fanout_on_child(monkeypatch):
    from argus.github_client import GitHubError
    from argus.signals import contract as contract_mod

    contract_mod._controller_repo_names.cache_clear()
    monkeypatch.setattr(contract_mod, "_controller_repo_names", lambda: frozenset({"argus"}))

    class C:
        def get(self, path: str):
            raise GitHubError("skip")

    with patch("argus.rules_sync.rules_stale", return_value=True):
        child = RepoRecord("o/child", "o", "child")
        ctrl = RepoRecord("o/Argus", "o", "Argus")
        out_child = contract_mod.collect(C(), child)  # type: ignore[arg-type]
        out_ctrl = contract_mod.collect(C(), ctrl)  # type: ignore[arg-type]
    assert out_child["RULES-STALE"] is False
    assert out_child["rules_stale"] is False
    assert out_ctrl["RULES-STALE"] is True
    assert out_ctrl["is_controller"] is True


def test_release_token_not_required_by_default(monkeypatch):
    from argus.github_client import GitHubError
    from argus.signals import contract as contract_mod

    monkeypatch.delenv("ARGUS_REQUIRE_RELEASE_TOKEN", raising=False)
    monkeypatch.delenv("RELEASE_TOKEN", raising=False)
    monkeypatch.delenv("ARGUS_RELEASE_TOKEN", raising=False)

    class C:
        def get(self, path: str):
            if "workflows" in path:
                return [{"name": "release.yml"}]
            raise GitHubError("skip")

    child = RepoRecord("o/app", "o", "app")
    out = contract_mod.collect(C(), child)  # type: ignore[arg-type]
    # Free-tier: release_token_set forced true / no workflow flag → SEC applies_when false
    assert out["release_token_set"] is True
    assert out["has_release_workflow"] is False


def test_apply_api_handlers_runs_human_class_dependabot(tmp_path, monkeypatch):
    monkeypatch.setenv("ARGUS_ACTIONS_UNAVAILABLE", "0")
    store = StateStore(tmp_path / "s.sqlite")
    plan = _plan(
        "o/r",
        MatchedFix(fix=_fix("SEC-OPEN-DEPENDABOT-ALERTS", FixClass.HUMAN), reason="x"),
    )
    client = MagicMock()
    client.report_only = False
    called = {"n": 0}

    def _dep(client, plan, matched):
        called["n"] += 1
        return "https://example.test/pr/1"

    with patch.dict("argus.yolo.YOLO_HANDLERS", {"SEC-OPEN-DEPENDABOT-ALERTS": _dep}):
        result = apply_yolo_extras(
            client,
            store,
            [plan],
            dry_run=False,
            max_actions=10,
            yolo_cfg={"apply_api_handlers": True},
        )
    assert called["n"] == 1
    assert any("SEC-OPEN-DEPENDABOT-ALERTS" in a for a in result.applied)
    store.close()


def test_ci_soft_resolve_when_actions_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("ARGUS_ACTIONS_UNAVAILABLE", "1")
    store = StateStore(tmp_path / "s2.sqlite")
    plan = _plan(
        "o/r",
        MatchedFix(fix=_fix("CI-LATEST-FAILED", FixClass.AGENT), reason="red"),
    )
    client = MagicMock()
    client.report_only = False
    with patch("argus.actions_billing.actions_unavailable", return_value=True):
        result = apply_yolo_extras(
            client,
            store,
            [plan],
            dry_run=False,
            max_actions=10,
            yolo_cfg={"resolve_ci_when_actions_unavailable": True},
        )
    assert any("CI-LATEST-FAILED" in a for a in result.applied)
    store.close()


def test_ci_not_soft_resolved_when_actions_up(tmp_path, monkeypatch):
    monkeypatch.delenv("ARGUS_ACTIONS_UNAVAILABLE", raising=False)
    store = StateStore(tmp_path / "s3.sqlite")
    plan = _plan(
        "o/r",
        MatchedFix(fix=_fix("CI-LATEST-FAILED", FixClass.AGENT), reason="red"),
    )
    client = MagicMock()
    client.report_only = False
    with patch("argus.actions_billing.actions_unavailable", return_value=False):
        result = apply_yolo_extras(
            client,
            store,
            [plan],
            dry_run=False,
            max_actions=10,
            yolo_cfg={"resolve_ci_when_actions_unavailable": True},
        )
    assert not any("CI-LATEST-FAILED" in a for a in result.applied)
    assert any("needs_triage" in s for s in result.skipped)
    store.close()


def test_judgment_brand_not_auto_applied(tmp_path):
    store = StateStore(tmp_path / "s4.sqlite")
    plan = _plan(
        "o/r",
        MatchedFix(fix=_fix("BRAND-ICON-MISSING", FixClass.HUMAN), reason="x"),
    )
    client = MagicMock()
    client.report_only = False
    result = apply_yolo_extras(
        client,
        store,
        [plan],
        dry_run=False,
        max_actions=10,
        yolo_cfg={"apply_api_handlers": True},
    )
    assert any("judgment" in s for s in result.skipped)
    assert not any("BRAND-ICON-MISSING" in a for a in result.applied)
    store.close()


def test_codeql_agent_is_deterministic():
    m = MatchedFix(fix=_fix("SEC-CODEQL", FixClass.AGENT), reason="x")
    assert is_yolo_deterministic_agent(m)
    assert "SEC-CODEQL" in YOLO_API_SAFE_HANDLERS


def test_handlers_cfg_vanilla_enables_api():
    from argus.pipeline import _handlers_cfg

    cfg = _handlers_cfg(
        {
            "yolo": {"apply_api_handlers": False, "resolve_ci_when_actions_unavailable": True},
            "normal": {"yolo_handlers": True, "continuous_zero": True},
        },
        yolo_on=False,
    )
    assert cfg["apply_api_handlers"] is True
