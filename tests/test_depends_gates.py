from __future__ import annotations

from argus.compose import _topo_phases
from argus.config_loader import load_fixes
from argus.models import FixClass, MatchedFix
from argus.pipeline import build_plans_from_fixtures
from tests.conftest import load_fixture


def test_depends_on_orders_before_dependent():
    fixes = {f.id: f for f in load_fixes()}
    presentation = fixes["AGENT-PRESENTATION"]
    # Synthetic list: dependent first, dependency second — topo should flip when both present
    dep_id = presentation.depends_on[0]
    matched = [
        MatchedFix(fix=presentation),
        MatchedFix(fix=fixes[dep_id]),
    ]
    phases = _topo_phases(matched)
    flat = [m.fix.id for items in phases.values() for m in items]
    assert flat.index(dep_id) < flat.index("AGENT-PRESENTATION")


def test_every_agent_and_auto_fix_has_gate():
    for fix in load_fixes():
        if fix.class_ in (FixClass.AGENT, FixClass.AUTO_SAFE):
            assert fix.gate, fix.id


def test_archived_scoring_categories_only():
    from argus.config_loader import load_rubric
    from argus.models import RepoStatus
    from argus.score import score_repo
    from argus.signals import fixture_bundle

    data = load_fixture("archived.json")
    result = score_repo(fixture_bundle(data["signals"]), load_rubric(), RepoStatus.ARCHIVED)
    assert set(result.category_scores) <= {"hygiene", "security"}


def test_experimental_fixture_composes():
    plan = build_plans_from_fixtures([load_fixture("experimental.json")])[0]
    assert plan.repo.status.value == "experimental"
    assert plan.human_fixes or plan.auto_fixes or plan.agent_fixes
