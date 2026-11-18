"""Dependabot alert-pause risk signal + fix match."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from argus.config_loader import load_fixes
from argus.github_client import GitHubError
from argus.match import match_fixes
from argus.models import RepoRecord, RepoStatus
from argus.signals import deps, fixture_bundle


def _repo(*, days: int | None, status: RepoStatus = RepoStatus.ACTIVE) -> RepoRecord:
    raw: dict = {}
    if days is not None:
        when = datetime.now(UTC) - timedelta(days=days)
        raw["pushed_at"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    return RepoRecord(
        full_name="alice/app",
        owner="alice",
        name="app",
        status=status,
        raw=raw,
    )


def _client() -> MagicMock:
    client = MagicMock()

    def _get(path, **_kw):
        if "vulnerability-alerts" in path:
            raise GitHubError("404")
        if "dependabot/alerts" in path:
            raise GitHubError("403")
        if "contents" in path:
            raise GitHubError("404")
        return {}

    client.get.side_effect = _get
    return client


def test_deps_flags_pause_risk_at_300_days():
    client = _client()
    out = deps.collect(client, _repo(days=300))
    assert out["dependabot_alert_pause_risk"] is True
    assert out["days_since_push"] >= 300
    fresh = deps.collect(client, _repo(days=30))
    assert fresh["dependabot_alert_pause_risk"] is False


def test_pause_risk_fix_matches_when_alerts_on():
    fixes = [f for f in load_fixes() if f.id == "SEC-DEPENDABOT-ALERT-PAUSE-RISK"]
    assert fixes
    repo = _repo(days=310)
    hit = fixture_bundle(
        {
            "deps": {
                "vulnerability_alerts_enabled": True,
                "dependabot_alert_pause_risk": True,
                "open_dependabot_alerts": 0,
            }
        }
    )
    matched = match_fixes(fixes, repo, hit, store=None, profile="edward")
    assert [m.fix.id for m in matched] == ["SEC-DEPENDABOT-ALERT-PAUSE-RISK"]
    miss = fixture_bundle(
        {
            "deps": {
                "vulnerability_alerts_enabled": False,
                "dependabot_alert_pause_risk": True,
            }
        }
    )
    assert match_fixes(fixes, repo, miss, store=None, profile="edward") == []
