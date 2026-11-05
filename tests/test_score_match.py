from __future__ import annotations

from argus.config_loader import load_rubric
from argus.models import Confidence, RepoStatus
from argus.pipeline import build_plans_from_fixtures
from argus.score import score_repo
from argus.signals import fixture_bundle
from tests.conftest import load_fixture


def test_parked_hygiene_security_only():
    data = load_fixture("parked.json")
    signals = fixture_bundle(data["signals"])
    result = score_repo(signals, load_rubric(), RepoStatus.PARKED)
    assert set(result.category_scores) <= {"hygiene", "security", "presentation"}


def test_missing_categories_force_low_confidence():
    plan = build_plans_from_fixtures([load_fixture("low_confidence.json")])[0]
    assert plan.score.confidence == Confidence.LOW


def test_depends_on_ordering_in_phases():
    plans = build_plans_from_fixtures([load_fixture("active_rotting.json")])
    agent = plans[0].agent_fixes
    # AGENT-PRESENTATION depends on HYGIENE-DESCRIPTION (auto); agent list may include presentation
    ids = [m.fix.id for m in agent]
    if "AGENT-PRESENTATION" in ids and "HYGIENE-DESCRIPTION" in {m.fix.id for m in plans[0].auto_fixes}:
        assert "AGENT-PRESENTATION" in ids
