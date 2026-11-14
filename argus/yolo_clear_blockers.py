"""Mandatory YOLO upgrade clear loop: fix → wait → soft-merge until green or hard leftover."""

from __future__ import annotations

import time
from typing import Any

from argus.config_loader import load_safety
from argus.dependabot_policy import allowed_levels as dependabot_levels
from argus.github_client import GitHubClient
from argus.yolo import (
    YoloResult,
    merge_argus_prs,
    merge_dependabot_prs,
    merge_upgrade_prs,
)
from argus.yolo_upgrade_fix import fix_open_upgrade_prs


def clear_open_upgrade_blockers(
    client: GitHubClient,
    *,
    login: str | None = None,
    max_merges: int = 80,
    loops: int = 8,
    sleep_s: int = 90,
    soft_allowlist: bool = True,
    require_armed: bool = True,
    also_dependabot_patch: bool = True,
    also_argus_prs: bool = True,
    safety: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Exhaust mechanical upgrade/patch/argus merges while CI settles.

    Soft-merge stays allowlist-only (security/Trivy/CodeQL still hard-block).
    Re-runs fixers each round so new check failures get another mechanical pass.
    """
    out: dict[str, Any] = {
        "rounds": [],
        "merged": [],
        "dep_merged": [],
        "argus_merged": [],
        "leftovers": [],
        "fix": [],
    }
    remaining = max(1, max_merges)
    for i in range(max(1, loops)):
        fix = fix_open_upgrade_prs(client, login=login, max_repos=remaining)
        out["fix"].append({"pass": i + 1, **{k: fix.get(k) for k in ("fixed", "skipped", "errors")}})
        up = merge_upgrade_prs(
            client,
            max_merges=remaining,
            login=login,
            require_armed=require_armed,
            soft_allowlist=soft_allowlist,
        )
        argus: YoloResult | None = None
        if also_argus_prs:
            rem_a = max(0, remaining - len(up.merged))
            argus = merge_argus_prs(
                client,
                max_merges=rem_a,
                login=login,
                require_armed=require_armed,
                soft_allowlist=soft_allowlist,
            )
        dep: YoloResult | None = None
        if also_dependabot_patch:
            used = len(up.merged) + (len(argus.merged) if argus else 0)
            rem_dep = max(0, remaining - used)
            safety_cfg = safety or load_safety()
            dep = merge_dependabot_prs(
                client,
                max_merges=rem_dep,
                login=login,
                safety=safety_cfg,
                require_armed=require_armed,
                allowed_levels=dependabot_levels(safety_cfg, yolo=True),
            )
        round_row = {
            "pass": i + 1,
            "merged": list(up.merged),
            "skipped": list(up.skipped) + (list(argus.skipped) if argus else []),
            "errors": list(up.errors) + (list(argus.errors) if argus else []),
            "argus_merged": list(argus.merged) if argus else [],
            "dep_merged": list(dep.merged) if dep else [],
        }
        out["rounds"].append(round_row)
        out["merged"].extend(up.merged)
        if argus:
            out["argus_merged"].extend(argus.merged)
        if dep:
            out["dep_merged"].extend(dep.merged)
        remaining = max(
            0,
            remaining
            - len(up.merged)
            - (len(argus.merged) if argus else 0)
            - (len(dep.merged) if dep else 0),
        )
        hard = [
            s
            for s in (list(up.skipped) + (list(argus.skipped) if argus else []))
            if "ci_green" in s
            and ":pending" not in s
            and ":soft_allowlist" not in s
            and ":actions_billing" not in s
            and ":actions_unavailable" not in s
        ]
        pending = any(
            ":pending" in s
            for s in (list(up.skipped) + (list(argus.skipped) if argus else []))
        )
        fixed_any = bool(fix.get("fixed"))
        out["leftovers"] = hard
        if remaining <= 0:
            break
        if (
            not pending
            and not fixed_any
            and not up.merged
            and not (argus and argus.merged)
            and not (dep and dep.merged)
        ):
            # Steady state: nothing pending, nothing newly fixed/merged.
            break
        if i + 1 >= loops:
            break
        time.sleep(max(5, sleep_s))
    return out
