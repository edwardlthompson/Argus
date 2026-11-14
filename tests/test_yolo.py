from __future__ import annotations

from argus.health import clear_auto_fixes_for_repos
from argus.pipeline import build_plans_from_fixtures
from argus.yolo import (
    YOLO_HANDLERS,
    is_dependabot_patch_title,
    is_yolo_closable_stale_pr,
)
from tests.conftest import load_fixture


def test_pr_stale_closes_only_bot_or_argus_heads():
    assert is_yolo_closable_stale_pr("chore/argus-sec-codeql", "edwardlthompson")
    assert is_yolo_closable_stale_pr("dependabot/npm_and_yarn/foo", "dependabot[bot]")
    assert not is_yolo_closable_stale_pr("feature/login", "alice")


def test_yolo_handlers_cover_cleanup_ids():
    for fid in (
        "SEC-CODEQL",
        "SEC-OPEN-DEPENDABOT-ALERTS",
        "BRAND-ICON-MISSING",
        "LINEAGE-RECOMMEND-UPGRADE",
        "AGENT-WHAT-NOT",
        "AGENT-MEMORY-LAYOUT",
        "BOARD-RESTRUCTURE",
    ):
        assert fid in YOLO_HANDLERS


def test_brand_handler_is_brief_only_not_png_gen():
    import inspect

    from argus.yolo import _brand_icon

    src = inspect.getsource(_brand_icon)
    assert "generate_icon_png" not in src
    assert "design brief" in src.lower() or "BRAND_ICON_BRIEF" in src


def test_dependabot_patch_filter():
    from argus.yolo import is_dependabot_auto_mergeable

    assert is_dependabot_patch_title(
        "Bump requests from 2.31.0 to 2.32.1",
        "dependabot[bot]",
    )
    assert is_dependabot_patch_title(
        "Bump left-pad from 1.0.0 to 1.1.0",
        "dependabot[bot]",
    )
    assert not is_dependabot_patch_title(
        "Bump left-pad from 1.0.0 to 2.0.0",
        "dependabot[bot]",
    )
    assert not is_dependabot_patch_title(
        "Bump foo (major)",
        "dependabot[bot]",
    )
    assert not is_dependabot_patch_title(
        "feat: redesign homepage",
        "alice",
    )
    assert is_dependabot_auto_mergeable(
        "chore(deps): bump actions/checkout from 4 to 7",
        "dependabot[bot]",
        levels=("patch", "minor", "major"),
    )
    assert not is_dependabot_auto_mergeable(
        "chore(deps): bump actions/checkout from 4 to 7",
        "dependabot[bot]",
        levels=("patch", "minor"),
    )
    assert is_dependabot_auto_mergeable(
        "chore(deps): update httpx requirement from >=0.27 to >=0.28.1",
        "dependabot[bot]",
        levels=("patch", "minor", "major"),
    )


def test_skip_profile_clears_human_and_agent():
    plans = build_plans_from_fixtures([load_fixture("human_only.json")])
    name = plans[0].repo.full_name
    # Ensure there is something to clear
    assert plans[0].human_fixes or plans[0].auto_fixes or plans[0].agent_fixes
    clear_auto_fixes_for_repos(plans, {name})
    assert plans[0].human_fixes == []
    assert plans[0].agent_fixes == []
    assert plans[0].auto_fixes == []
