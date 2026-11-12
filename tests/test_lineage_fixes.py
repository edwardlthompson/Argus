from __future__ import annotations

from argus.pipeline import build_plans_from_fixtures


def test_lineage_version_stale_matches():
    fixture = {
        "repo": {
            "full_name": "example/child",
            "status": "active",
            "description": "Child of bootstrap",
            "topics": ["python", "tool", "cli"],
            "can_write": True,
        },
        "signals": {
            "momentum": {"days_since_push": 1, "open_issues": 0, "stargazers": 0, "fork": False},
            "responsiveness": {"open_issue_sample": 0, "stale_issues_90d": 0},
            "ci": {"has_workflows": True, "latest_failed": False},
            "deps": {
                "vulnerability_alerts_enabled": True,
                "has_dependabot_config": True,
                "open_dependabot_alerts": 0,
            },
            "presentation": {
                "description": "Child of bootstrap",
                "description_len": 18,
                "topics": ["python", "tool", "cli"],
                "specific_topic_count": 3,
                "has_readme": True,
                "has_what_not_section": True,
            },
            "hygiene": {
                "security_md": True,
                "contributing_md": True,
                "code_of_conduct_md": True,
                "gitattributes": True,
                "license_file": True,
                "agent_files_at_root": False,
            },
            "security": {
                "secret_scanning_enabled": True,
                "private": False,
                "archived": False,
                "codeql_likely": True,
            },
            "lineage": {
                "is_template_child": True,
                "has_template_version": True,
                "template_version": "1.0.0",
                "expected_version": "1.12.0",
                "version_behind": True,
                "missing_lineage_files": [],
                "points_upstream": True,
            },
        },
    }
    plan = build_plans_from_fixtures([fixture])[0]
    auto_ids = {m.fix.id for m in plan.auto_fixes}
    agent_ids = {m.fix.id for m in plan.agent_fixes}
    assert "LINEAGE-VERSION-STALE" in auto_ids
    assert "LINEAGE-RECOMMEND-UPGRADE" in agent_ids
