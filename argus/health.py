"""Portfolio health snapshots and before/after deltas (deterministic)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from argus.models import RepoPlan
from argus.paths import DIST_DIR, ensure_runtime_dirs


def clear_auto_fixes_for_repos(plans: list[RepoPlan], full_names: set[str]) -> None:
    """Drop mutative matches for repos that must not be changed (e.g. profile Overview)."""
    for plan in plans:
        if plan.repo.full_name in full_names:
            plan.auto_fixes = []
            plan.human_fixes = []
            plan.agent_fixes = []


def project_plans_after_apply(
    plans: list[RepoPlan],
    apply_summary: dict[str, Any],
    *,
    dry_run: bool,
) -> list[RepoPlan]:
    """Copy-free projection: remove auto fixes that were applied or would be (dry-run)."""
    drop: set[str] = set(apply_summary.get("applied") or [])
    if dry_run:
        for row in apply_summary.get("would_prs") or []:
            drop.add(f"{row.get('repo')}:{row.get('fix')}")
    if not drop:
        return plans
    for plan in plans:
        plan.auto_fixes = [
            m
            for m in plan.auto_fixes
            if f"{plan.repo.full_name}:{m.fix.id}" not in drop
        ]
    return plans


def snapshot_plans(plans: list[RepoPlan]) -> dict[str, Any]:
    repos: list[dict[str, Any]] = []
    for plan in sorted(plans, key=lambda p: p.repo.full_name.lower()):
        repos.append(
            {
                "repo": plan.repo.full_name,
                "attention": plan.score.attention,
                "confidence": plan.score.confidence.value,
                "auto": [m.fix.id for m in plan.auto_fixes],
                "agent": [m.fix.id for m in plan.agent_fixes],
                "human": [m.fix.id for m in plan.human_fixes],
            }
        )
    auto_n = sum(len(r["auto"]) for r in repos)
    agent_n = sum(len(r["agent"]) for r in repos)
    human_n = sum(len(r["human"]) for r in repos)
    att = [float(r["attention"]) for r in repos]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "repo_count": len(repos),
        "totals": {
            "auto_fixes": auto_n,
            "agent_fixes": agent_n,
            "human_fixes": human_n,
            "open_fixes": auto_n + agent_n + human_n,
            "mean_attention": round(sum(att) / len(att), 2) if att else 0.0,
            "max_attention": max(att) if att else 0.0,
        },
        "repos": repos,
    }


def compare_snapshots(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    apply_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bt = before.get("totals") or {}
    at = after.get("totals") or {}
    before_map = {r["repo"]: r for r in before.get("repos") or []}
    after_map = {r["repo"]: r for r in after.get("repos") or []}
    improved: list[dict[str, Any]] = []
    worsened: list[dict[str, Any]] = []
    for name in sorted(set(before_map) | set(after_map)):
        b = before_map.get(name) or {}
        a = after_map.get(name) or {}
        b_open = len(b.get("auto") or []) + len(b.get("agent") or []) + len(b.get("human") or [])
        a_open = len(a.get("auto") or []) + len(a.get("agent") or []) + len(a.get("human") or [])
        b_att = float(b.get("attention") or 0)
        a_att = float(a.get("attention") or 0)
        row = {
            "repo": name,
            "attention_before": b_att,
            "attention_after": a_att,
            "open_before": b_open,
            "open_after": a_open,
            "delta_attention": round(a_att - b_att, 2),
            "delta_open": a_open - b_open,
        }
        if a_att < b_att or a_open < b_open:
            improved.append(row)
        elif a_att > b_att or a_open > b_open:
            worsened.append(row)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "totals_before": bt,
        "totals_after": at,
        "delta_open_fixes": int(at.get("open_fixes") or 0) - int(bt.get("open_fixes") or 0),
        "delta_mean_attention": round(
            float(at.get("mean_attention") or 0) - float(bt.get("mean_attention") or 0), 2
        ),
        "improved": improved,
        "worsened": worsened,
        "apply": apply_summary or {},
        "note": (
            "Open-fix counts drop when signals clear (often after auto_safe PRs merge). "
            "Apply opens PRs; unmerged PRs may leave after scores unchanged."
        ),
    }


def compose_delta_markdown(delta: dict[str, Any]) -> str:
    bt = delta.get("totals_before") or {}
    at = delta.get("totals_after") or {}
    apply = delta.get("apply") or {}
    lines = [
        "# Argus health delta",
        "",
        f"Generated: {delta.get('generated_at', '')}",
        "",
        "## Totals",
        "",
        "| Metric | Before | After | Delta |",
        "|--------|--------|-------|-------|",
        f"| Open fixes | {bt.get('open_fixes', 0)} | {at.get('open_fixes', 0)} | "
        f"{delta.get('delta_open_fixes', 0)} |",
        f"| Auto-safe | {bt.get('auto_fixes', 0)} | {at.get('auto_fixes', 0)} | — |",
        f"| Human | {bt.get('human_fixes', 0)} | {at.get('human_fixes', 0)} | — |",
        f"| Agent | {bt.get('agent_fixes', 0)} | {at.get('agent_fixes', 0)} | — |",
        f"| Mean attention | {bt.get('mean_attention', 0)} | {at.get('mean_attention', 0)} | "
        f"{delta.get('delta_mean_attention', 0)} |",
        "",
        "## Fixes applied this run",
        "",
    ]
    opened = apply.get("opened_prs") or []
    applied = apply.get("applied") or []
    would = apply.get("would_prs") or []
    if applied:
        lines.append("Applied:")
        for a in applied:
            lines.append(f"- `{a}`")
        lines.append("")
    if opened:
        lines.append("PRs opened:")
        for u in opened:
            lines.append(f"- {u}")
        lines.append("")
    if would and not applied:
        lines.append("Would open (dry-run):")
        for w in would:
            lines.append(f"- `{w.get('repo')}` / `{w.get('fix')}`")
        lines.append("")
    if not applied and not would:
        lines.append("_No auto_safe apply actions._")
        lines.append("")
    if delta.get("note"):
        lines.extend([f"> {delta['note']}", ""])
    improved = delta.get("improved") or []
    if improved:
        lines.extend(["## Improved repos", ""])
        for row in improved[:40]:
            lines.append(
                f"- `{row['repo']}` attention {row['attention_before']}→{row['attention_after']} "
                f"(open {row['open_before']}→{row['open_after']})"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_health_artifacts(
    *,
    before: dict[str, Any],
    after: dict[str, Any],
    delta: dict[str, Any],
    dist_dir: Path | None = None,
) -> dict[str, str]:
    ensure_runtime_dirs()
    out = dist_dir or DIST_DIR
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "health_before": out / "health-before.json",
        "health_after": out / "health-after.json",
        "health_delta_json": out / "health-delta.json",
        "health_delta_md": out / "health-delta.md",
        "health": out / "health.json",
    }
    paths["health_before"].write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    paths["health_after"].write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    paths["health"].write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    paths["health_delta_json"].write_text(json.dumps(delta, indent=2) + "\n", encoding="utf-8")
    paths["health_delta_md"].write_text(compose_delta_markdown(delta), encoding="utf-8")
    prev = out / "health-previous.json"
    prev.write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}
