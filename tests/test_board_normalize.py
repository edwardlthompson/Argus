from __future__ import annotations

from argus.board_classify import classify_board, locate_board_path, missing_markers
from argus.board_normalize import append_missing_markers, restructure_divergent
from argus.pipeline import build_plans_from_fixtures

HERMES_LIKE = """# Build Plan

<!-- remaining-tally -->
**Remaining:** AGENT 0 · **0 open**
<!-- /remaining-tally -->

Live board for Hermes. Format: `🔲 [AGENT] Short task`.

### Open PRs (synced)

<!-- open-prs-sync:begin -->
_No open Dependabot or Release Please PRs._
<!-- open-prs-sync:end -->

### Template gaps (synced)

<!-- template-gaps-sync:begin -->
_No template gaps._
<!-- template-gaps-sync:end -->
"""

QRAFT_LIKE = """# Build Plan

> QRaft task board.

1. 🔲 [HUMAN] Confirm Pages URL after first green deploy
2. 🔲 [AGENT] Restore examples/web
"""

NEWS_PARTIAL = (
    HERMES_LIKE
    + """
## News inbox (synced)

- 🔲 [AGENT] Flag idle Dependabot pause — scope: argus/signals
- 🔲 [HUMAN] Review issue types for triage
"""
)


def test_locate_prefers_root():
    assert locate_board_path(root_exists=True, docs_exists=True) == "BUILD_PLAN.md"
    assert locate_board_path(root_exists=False, docs_exists=True) == "docs/BUILD_PLAN.md"
    assert locate_board_path(root_exists=False, docs_exists=False) is None


def test_partial_hermes_like_missing_lanes():
    info = classify_board(HERMES_LIKE, "BUILD_PLAN.md")
    assert info["kind"] == "partial"
    assert "local-agent-lane" in info["missing_markers"]
    assert "cloud-agent-lane" in info["missing_markers"]
    assert "remaining-tally" not in info["missing_markers"]


def test_divergent_qraft_like():
    info = classify_board(QRAFT_LIKE, "BUILD_PLAN.md")
    assert info["kind"] == "divergent"
    assert info["looks_apb"] is False


def test_docs_only_flag():
    info = classify_board(QRAFT_LIKE, "docs/BUILD_PLAN.md")
    assert info["docs_only"] is True


def test_append_markers_and_fold_news():
    out = append_missing_markers(NEWS_PARTIAL)
    assert "local-agent-lane" in out
    assert "cloud-agent-lane" in out
    assert "News inbox (synced)" not in out
    assert "[AGENT][LOCAL]" in out
    assert "Waiting on a person" in out
    assert "Review issue types" in out
    assert not missing_markers(out)


def test_restructure_preserves_open_and_writes_root():
    files = restructure_divergent(
        QRAFT_LIKE, source_path="docs/BUILD_PLAN.md", has_completed_tasks=True
    )
    assert "BUILD_PLAN.md" in files
    assert "docs/BUILD_PLAN.md" in files
    root = files["BUILD_PLAN.md"]
    assert "Confirm Pages URL" in root
    assert "Restore examples/web" in root
    assert "[AGENT][LOCAL]" in root
    assert "COMPLETED_TASKS.md" in root
    assert "Previous board" in root
    assert files["docs/BUILD_PLAN.md"].startswith("# BUILD_PLAN moved")
    assert not missing_markers(root)


def test_fixes_match_kinds():
    partial = {
        "repo": {
            "full_name": "example/partial-board",
            "status": "active",
            "description": "Child",
            "topics": ["python", "tool", "cli"],
            "can_write": True,
        },
        "signals": _green_signals(
            board={
                "kind": "partial",
                "path": "BUILD_PLAN.md",
                "missing_markers": ["local-agent-lane"],
                "has_news_inbox": True,
                "docs_only": False,
                "looks_apb": True,
            }
        ),
    }
    divergent = {
        "repo": {
            "full_name": "example/divergent-board",
            "status": "active",
            "description": "Child",
            "topics": ["python", "tool", "cli"],
            "can_write": True,
        },
        "signals": _green_signals(
            board={
                "kind": "divergent",
                "path": "docs/BUILD_PLAN.md",
                "missing_markers": ["remaining-tally", "local-agent-lane"],
                "has_news_inbox": False,
                "docs_only": True,
                "looks_apb": False,
            }
        ),
    }
    p = build_plans_from_fixtures([partial])[0]
    d = build_plans_from_fixtures([divergent])[0]
    assert "BOARD-MARKERS" in {m.fix.id for m in p.auto_fixes}
    assert "BOARD-RESTRUCTURE" not in {m.fix.id for m in p.agent_fixes}
    assert "BOARD-RESTRUCTURE" in {m.fix.id for m in d.agent_fixes}
    assert "BOARD-MARKERS" not in {m.fix.id for m in d.auto_fixes}


def _green_signals(*, board: dict) -> dict:
    return {
        "momentum": {"days_since_push": 1, "open_issues": 0, "stargazers": 0, "fork": False},
        "responsiveness": {"open_issue_sample": 0, "stale_issues_90d": 0},
        "ci": {"has_workflows": True, "latest_failed": False},
        "deps": {
            "vulnerability_alerts_enabled": True,
            "has_dependabot_config": True,
            "open_dependabot_alerts": 0,
        },
        "presentation": {
            "description": "Child",
            "description_len": 5,
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
        "board": board,
    }
