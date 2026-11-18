from __future__ import annotations

from unittest.mock import MagicMock

from argus.dependabot_policy import (
    allowed_levels,
    bump_allowed,
    classify_dependabot_bump,
    merge_enabled,
)
from argus.yolo import merge_dependabot_prs, pr_ci_detail


def test_classify_levels():
    bot = "dependabot[bot]"
    assert classify_dependabot_bump("Bump requests from 2.31.0 to 2.32.1", bot) == "minor"
    assert classify_dependabot_bump("Bump left-pad from 1.0.0 to 1.0.1", bot) == "patch"
    assert classify_dependabot_bump("Bump left-pad from 1.0.0 to 2.0.0", bot) == "major"
    assert classify_dependabot_bump("Bump foo (major)", bot) == "major"
    assert classify_dependabot_bump("chore(deps): bump actions/checkout from 4 to 7", bot) == "major"
    assert classify_dependabot_bump("feat: redesign homepage", "alice") is None


def test_vanilla_rejects_major_yolo_allows():
    major = classify_dependabot_bump("Bump left-pad from 1.0.0 to 2.0.0", "dependabot[bot]")
    assert not bump_allowed(major, ("patch", "minor"))
    assert bump_allowed(major, ("patch", "minor", "major"))


def test_safety_levels_and_aliases():
    safety = {
        "normal": {"merge_dependabot": True, "dependabot_auto_merge_levels": ["patch", "minor"]},
        "yolo": {
            "auto_merge_dependabot": True,
            "dependabot_auto_merge_levels": ["patch", "minor", "major"],
        },
    }
    assert allowed_levels(safety, yolo=False) == ["patch", "minor"]
    assert allowed_levels(safety, yolo=True) == ["patch", "minor", "major"]
    assert merge_enabled(safety, yolo=False) is True
    assert merge_enabled({"normal": {"merge_dependabot_patch": False}}, yolo=False) is False
    assert merge_enabled({"yolo": {"auto_merge_dependabot_patch": False}}, yolo=True) is False


def _client(*, checks: list[dict] | None, title: str = "Bump foo from 1.0.0 to 1.0.1"):
    client = MagicMock()
    client.report_only = False
    client.whoami.return_value = {"login": "me"}

    def _get(path, params=None):
        if path == "/search/issues":
            return {
                "items": [
                    {
                        "number": 1,
                        "title": title,
                        "user": {"login": "dependabot[bot]"},
                        "repository_url": "https://api.github.com/repos/o/r",
                        "html_url": "https://github.com/o/r/pull/1",
                    }
                ]
            }
        if path.endswith("/pulls/1"):
            return {"head": {"sha": "abc", "ref": "dependabot/pip/foo"}}
        if "check-runs" in path:
            return {"check_runs": checks}
        if path.endswith("/status"):
            return {}
        return {}

    client.get.side_effect = _get
    return client


_ARMED = {
    "apply_mode": "yolo",
    "never_force_push": True,
    "never_delete_repos": True,
    "prefer_pull_requests": True,
    "yolo": {"skip_profile": True, "auto_merge_dependabot": True},
    "normal": {"merge_dependabot": True, "dependabot_auto_merge_levels": ["patch", "minor"]},
}


def test_merge_requires_green_checks(tmp_path, monkeypatch):
    monkeypatch.setattr("argus.yolo_arm.is_yolo_armed", lambda safety=None, root=None: True)
    monkeypatch.setattr("argus.yolo_checks.is_yolo_armed", lambda safety=None, root=None: True)
    green = _client(checks=[{"status": "completed", "conclusion": "success", "name": "ci"}])
    result = merge_dependabot_prs(
        green,
        max_merges=5,
        safety=_ARMED,
        require_armed=True,
        allowed_levels=["patch", "minor", "major"],
    )
    assert result.merged == ["o/r#1"]
    green.put.assert_called()


def test_merge_skips_when_ci_never_started(tmp_path, monkeypatch):
    monkeypatch.setattr("argus.yolo_arm.is_yolo_armed", lambda safety=None, root=None: True)
    monkeypatch.setattr("argus.yolo_checks.is_yolo_armed", lambda safety=None, root=None: True)
    empty = _client(checks=[])
    result = merge_dependabot_prs(
        empty,
        max_merges=5,
        safety=_ARMED,
        require_armed=True,
        allowed_levels=["patch", "minor"],
    )
    assert result.merged == []
    assert any("ci_green" in s for s in result.skipped)
    empty.put.assert_not_called()


def test_vanilla_skips_major_even_when_green(tmp_path, monkeypatch):
    monkeypatch.setattr("argus.yolo_arm.is_yolo_armed", lambda safety=None, root=None: False)
    monkeypatch.setattr("argus.yolo_checks.is_yolo_armed", lambda safety=None, root=None: False)
    client = _client(
        checks=[{"status": "completed", "conclusion": "success", "name": "ci"}],
        title="Bump left-pad from 1.0.0 to 2.0.0",
    )
    result = merge_dependabot_prs(
        client,
        max_merges=5,
        safety=_ARMED,
        require_armed=False,
        allowed_levels=["patch", "minor"],
    )
    assert result.merged == []
    assert any("level=major" in s for s in result.skipped)
    client.put.assert_not_called()


def test_pr_ci_empty_as_unknown():
    client = MagicMock()
    client.get.side_effect = lambda path, params=None: (
        {"check_runs": []} if "check-runs" in path else {}
    )
    detail = pr_ci_detail(client, "o", "r", "abc", empty_as="unknown")
    assert detail["state"] == "unknown"
    detail_green = pr_ci_detail(client, "o", "r", "abc")
    assert detail_green["state"] == "green"
