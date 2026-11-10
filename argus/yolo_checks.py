"""Six pre-merge checks for private-runner YOLO (hands-off but gated)."""

from __future__ import annotations

from typing import Any

from argus.yolo_arm import is_yolo_armed

# Stable names for doctor / docs / tests.
PRE_MERGE_CHECKS = (
    "armed",
    "hard_floors",
    "prefer_prs",
    "title_policy",
    "ci_green",
    "not_profile_sacred",
)


def evaluate_pre_merge(
    *,
    safety: dict[str, Any] | None,
    title: str,
    ci_green: bool,
    is_profile_repo: bool,
    skip_profile: bool = True,
    root=None,
) -> tuple[bool, list[str]]:
    """Return (ok, failed_check_ids)."""
    failed: list[str] = []
    safety = safety or {}
    if not is_yolo_armed(safety, root=root):
        failed.append("armed")
    if not safety.get("never_force_push", True) or not safety.get("never_delete_repos", True):
        failed.append("hard_floors")
    if not safety.get("prefer_pull_requests", True):
        failed.append("prefer_prs")
    t = (title or "").lower()
    ok_title = t.startswith("chore(argus)") or "bump " in t or t.startswith("chore(deps)")
    if not ok_title:
        failed.append("title_policy")
    if not ci_green:
        failed.append("ci_green")
    if is_profile_repo and skip_profile:
        failed.append("not_profile_sacred")
    return (not failed, failed)
