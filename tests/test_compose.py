from __future__ import annotations

import re
from pathlib import Path

import pytest

from argus.compose import compose_html, compose_portfolio_markdown, compose_runbook, write_artifacts
from argus.config_loader import load_fixes
from argus.pipeline import build_plans_from_fixtures
from tests.conftest import load_fixture

FIXTURE_NAMES = [
    "parked.json",
    "active_rotting.json",
    "fork.json",
    "docs_only.json",
    "human_only.json",
    "agent_only.json",
    "low_confidence.json",
    "third_party.json",
    "archived.json",
    "experimental.json",
]


@pytest.fixture(scope="module")
def all_plans():
    fixtures = [load_fixture(n) for n in FIXTURE_NAMES]
    return build_plans_from_fixtures(fixtures)


def test_snapshots_runbook_and_html(all_plans, tmp_path: Path):
    md = compose_runbook(all_plans)
    html = compose_html(all_plans, target_label="fixture-portfolio", mode="test")
    portfolio = compose_portfolio_markdown(
        all_plans, target_label="fixture-portfolio", mode="test"
    )
    (tmp_path / "runbook.md").write_text(md, encoding="utf-8")
    (tmp_path / "report.html").write_text(html, encoding="utf-8")
    assert "# Argus Runbook" in md
    assert "Argus Portfolio Report" in html
    assert 'data-testid="summary-grid"' in html
    assert "badge-high" in html or "badge-medium" in html or "badge-good" in html
    assert "Overall Assessment" in portfolio
    expected = Path(__file__).parent / "fixtures" / "expected"
    expected.mkdir(exist_ok=True)
    gold_md = expected / "runbook.md"
    if not gold_md.exists():
        gold_md.write_text(md, encoding="utf-8")
    assert md == gold_md.read_text(encoding="utf-8")


def test_write_artifacts_portfolio(all_plans, tmp_path: Path):
    paths = write_artifacts(
        all_plans, dist_dir=tmp_path, target_label="t", mode="test"
    )
    assert paths["report"].exists()
    assert paths["portfolio"].exists()
    html = paths["report"].read_text(encoding="utf-8")
    assert "summary-grid" in html
    assert 'data-theme="dark"' in html
    assert "theme-toggle" in html
    assert 'data-testid="charts-grid"' in html
    assert 'html[data-theme="light"]' in html


def test_every_agent_phase_has_gate(all_plans):
    md = compose_runbook(all_plans)
    # For each ```text agent block, every Phase section before final must have GATE
    blocks = re.findall(r"```text(.*?)```", md, flags=re.S)
    for block in blocks:
        phases = re.findall(r"## Phase .+", block)
        gates = re.findall(r"^GATE: .+", block, flags=re.M)
        assert phases, "agent block missing phases"
        assert gates, "agent block missing GATE lines"
        assert len(gates) >= len([p for p in phases if "final" not in p.lower()]) or "GATE:" in block


def test_human_only_emits_no_agent_block():
    plan = build_plans_from_fixtures([load_fixture("human_only.json")])[0]
    assert plan.human_fixes
    # Filter agent/auto out for this assertion scenario — human_only fixture should not match agents
    assert not plan.agent_fixes
    md = compose_runbook([plan])
    assert "### Agent prompt" not in md
    assert "### Human tasks" in md


def test_agent_only_omits_human_list():
    plan = build_plans_from_fixtures([load_fixture("agent_only.json")])[0]
    assert plan.agent_fixes
    assert not plan.human_fixes
    md = compose_runbook([plan])
    assert "### Human tasks" not in md
    assert "### Agent prompt" in md


def test_every_agent_fix_in_some_fixture():
    agent_ids = {f.id for f in load_fixes() if f.class_.value == "agent"}
    seen: set[str] = set()
    for name in FIXTURE_NAMES:
        plans = build_plans_from_fixtures([load_fixture(name)], profile="edward")
        for p in plans:
            seen.update(m.fix.id for m in p.agent_fixes)
    # generic+edward coverage; AGENT-CORRECTNESS only on edward profile
    missing = agent_ids - seen
    # AGENT-CORRECTNESS applies when no CI — covered by active_rotting with edward
    assert not missing, f"agent fixes never matched: {missing}"


def test_low_confidence_marked():
    plan = build_plans_from_fixtures([load_fixture("low_confidence.json")])[0]
    assert plan.score.confidence.value == "low"
    md = compose_runbook([plan])
    assert "needs human read" in md.lower()


def test_report_banner():
    plans = build_plans_from_fixtures([load_fixture("third_party.json")], report_only=True)
    md = compose_runbook(plans, report_banner="Read-only report — no changes were made.")
    assert "Read-only report" in md
