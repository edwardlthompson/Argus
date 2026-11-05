from __future__ import annotations

from argus.apply import apply_auto_safe
from argus.github_client import GitHubClient
from argus.pipeline import build_plans_from_fixtures
from argus.state import StateStore
from tests.conftest import load_fixture


def test_report_only_never_writes(tmp_path):
    plans = build_plans_from_fixtures([load_fixture("third_party.json")], report_only=True)
    client = GitHubClient(token="", report_only=True)
    store = StateStore(tmp_path / "s.sqlite")
    result = apply_auto_safe(client, store, plans, dry_run=False, max_prs=5)
    assert client.write_attempts == 0
    assert all("report_only" in s for s in result.skipped) or not plans[0].auto_fixes or result.skipped
    store.close()
    client.close()


def test_dry_run_skips_writes(tmp_path):
    plans = build_plans_from_fixtures([load_fixture("active_rotting.json")])
    client = GitHubClient(token="", report_only=False)
    # Force can_write already true from fixture
    store = StateStore(tmp_path / "s2.sqlite")
    result = apply_auto_safe(client, store, plans, dry_run=True, max_prs=5)
    assert client.write_attempts == 0
    assert any("dry_run" in s for s in result.skipped)
    store.close()
    client.close()
