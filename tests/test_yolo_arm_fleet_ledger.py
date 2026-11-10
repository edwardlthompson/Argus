from __future__ import annotations

from pathlib import Path

from argus.action_ledger import append_action, record_actions
from argus.fleet import halt, is_halted, revert_brief, write_plan
from argus.quiet_log import format_run_line
from argus.yolo_arm import is_yolo_armed, shutdown_yolo
from argus.yolo_checks import PRE_MERGE_CHECKS, evaluate_pre_merge


def test_dual_plane_arm(tmp_path: Path):
    assert not is_yolo_armed({"apply_mode": "normal"}, root=tmp_path)
    (tmp_path / "yolo.on").write_text("1\n", encoding="utf-8")
    assert is_yolo_armed({"apply_mode": "normal"}, root=tmp_path)
    shutdown_yolo("test", root=tmp_path)
    assert not is_yolo_armed({"apply_mode": "yolo"}, root=tmp_path)
    assert (tmp_path / "YOLO-OFF.md").is_file()


def test_pre_merge_six_checks(tmp_path: Path):
    assert len(PRE_MERGE_CHECKS) == 6
    (tmp_path / "yolo.on").write_text("1\n", encoding="utf-8")
    ok, failed = evaluate_pre_merge(
        safety={
            "apply_mode": "normal",
            "never_force_push": True,
            "never_delete_repos": True,
            "prefer_pull_requests": True,
        },
        title="chore(argus): fix",
        ci_green=True,
        is_profile_repo=False,
        root=tmp_path,
    )
    assert ok and not failed
    ok2, failed2 = evaluate_pre_merge(
        safety={
            "apply_mode": "yolo",
            "never_force_push": True,
            "never_delete_repos": True,
            "prefer_pull_requests": True,
        },
        title="feat: redesign",
        ci_green=False,
        is_profile_repo=True,
        skip_profile=True,
        root=tmp_path,
    )
    assert not ok2
    assert "title_policy" in failed2
    assert "ci_green" in failed2
    assert "not_profile_sacred" in failed2


def test_upgrade_title_passes_policy(tmp_path: Path):
    (tmp_path / "yolo.on").write_text("1\n", encoding="utf-8")
    ok, failed = evaluate_pre_merge(
        safety={
            "apply_mode": "normal",
            "never_force_push": True,
            "never_delete_repos": True,
            "prefer_pull_requests": True,
        },
        title="chore(argus): upgrade parent rules to 1.13.0",
        ci_green=True,
        is_profile_repo=False,
        root=tmp_path,
    )
    assert ok and not failed


def test_action_ledger_and_fleet_revert(tmp_path: Path):
    append_action(
        actor="yolo",
        repo="o/r",
        action="applied",
        detail="SEC-CODEQL",
        brief_id="wave-1",
        sha_before="aaa",
        sha_after="bbb",
        dist_dir=tmp_path,
    )
    rows = record_actions(
        {"applied": ["o/r:FOO"], "opened_prs": ["https://example/pr/1"]},
        actor="fleet",
        brief_id="wave-1",
    )
    assert rows
    write_plan("wave-1", ["o/r"], verify="pytest", dist_dir=tmp_path)
    receipt = revert_brief("wave-1", dist_dir=tmp_path, dry_run=True)
    assert receipt["brief_id"] == "wave-1"
    assert receipt["steps"]
    halt("canary failed", root=tmp_path)
    assert is_halted(root=tmp_path)


def test_quiet_log_line():
    line = format_run_line(
        family="run", findings=3, files=12, checks=12, outcome="yolo"
    )
    assert line.startswith("argus run:")
    assert "findings=3" in line
