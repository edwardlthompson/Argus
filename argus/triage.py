"""Group open fixes by class for operator triage / fleet overview."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from argus.models import FixClass, RepoPlan


def group_by_fix_class(plans: list[RepoPlan]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {
        FixClass.AUTO_SAFE.value: [],
        FixClass.AGENT.value: [],
        FixClass.HUMAN.value: [],
    }
    for plan in plans:
        for m in plan.auto_fixes:
            buckets[FixClass.AUTO_SAFE.value].append(_row(plan, m))
        for m in plan.agent_fixes:
            buckets[FixClass.AGENT.value].append(_row(plan, m))
        for m in plan.human_fixes:
            buckets[FixClass.HUMAN.value].append(_row(plan, m))
    return buckets


def _row(plan: RepoPlan, m: Any) -> dict[str, Any]:
    return {
        "repo": plan.repo.full_name,
        "fix_id": m.fix.id,
        "title": m.fix.title,
        "class": m.fix.class_.value,
        "attention": plan.score.attention if plan.score else None,
    }


def summarize_triage(plans: list[RepoPlan]) -> dict[str, Any]:
    groups = group_by_fix_class(plans)
    by_id: dict[str, list[str]] = defaultdict(list)
    for _cls, rows in groups.items():
        for row in rows:
            by_id[row["fix_id"]].append(row["repo"])
    return {
        "repos": len(plans),
        "counts": {k: len(v) for k, v in groups.items()},
        "by_class": groups,
        "by_fix_id": {fid: sorted(set(repos)) for fid, repos in sorted(by_id.items())},
        "yolo_eligible_agent": [
            r for r in groups[FixClass.AGENT.value]
        ],
    }


def fleet_rollup(plans: list[RepoPlan]) -> dict[str, Any]:
    """Cross-repo rollup: fix id → repos (fleet triage view)."""
    base = summarize_triage(plans)
    return {
        "mode": "fleet",
        "repos": base["repos"],
        "counts": base["counts"],
        "by_fix_id": base["by_fix_id"],
        "agent_deterministic_count": base["counts"].get(FixClass.AGENT.value, 0),
        "human_count": base["counts"].get(FixClass.HUMAN.value, 0),
        "auto_safe_count": base["counts"].get(FixClass.AUTO_SAFE.value, 0),
    }
