"""Deterministic portfolio report view-model (no LLMs)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from argus.models import RepoPlan, RepoStatus

_PREFIX_ORDER = ("SEC", "HYGIENE", "CI", "LINEAGE", "AGENT", "PROF", "OTHER")


def _raw(plan: RepoPlan) -> dict[str, Any]:
    return plan.repo.raw or {}


def _meta_line(plan: RepoPlan) -> str:
    raw = _raw(plan)
    lic = raw.get("license") if isinstance(raw.get("license"), dict) else None
    spdx = str((lic or {}).get("spdx_id") or "unknown")
    lang = str(raw.get("language") or "—")
    stars = int(raw.get("stargazers_count") or 0)
    if "open_issues_only" in raw:
        issues = int(raw.get("open_issues_only") or 0)
    else:
        issues = int(raw.get("open_issues_count") or 0)
        if "open_prs_count" in raw:
            issues = max(0, issues - int(raw.get("open_prs_count") or 0))
    prs = int(raw.get("open_prs_count") or 0)
    pushed = str(raw.get("pushed_at") or "")[:10] or "—"
    pr_bit = f" · {prs} open PRs" if prs else ""
    return (
        f"{lang} · ★{stars} · License: {spdx} · {issues} open issues"
        f"{pr_bit} · Last push {pushed}"
    )


def _band(attention: float, open_any: bool) -> str:
    """Badge band for UI. No open Argus fixes → always good (score still shown)."""
    if not open_any:
        return "good"
    if attention >= 55:
        return "high"
    if attention >= 35:
        return "medium"
    return "good"


def _gh_open_issues(plan: RepoPlan) -> int:
    """True GitHub Issues only (PRs stripped). GitHub's open_issues_count includes PRs."""
    raw = _raw(plan)
    if "open_issues_only" in raw:
        return int(raw.get("open_issues_only") or 0)
    total = int(raw.get("open_issues_count") or 0)
    if "open_prs_count" in raw:
        return max(0, total - int(raw.get("open_prs_count") or 0))
    return total


def _gh_open_prs(plan: RepoPlan) -> int:
    """Open pull requests (never counted as Issues in Priority)."""
    return int(_raw(plan).get("open_prs_count") or 0)


def _argus_open_count(plan: RepoPlan) -> int:
    return len(plan.auto_fixes) + len(plan.agent_fixes) + len(plan.human_fixes)


def _needs_attention_listing(plan: RepoPlan) -> bool:
    """List repos with Argus fixes, Issues, or open PRs (PRs are not Issues)."""
    return (
        _argus_open_count(plan) > 0
        or _gh_open_issues(plan) > 0
        or _gh_open_prs(plan) > 0
    )


def _urgency_key(plan: RepoPlan) -> tuple[int, int, str]:
    """Most Issues first, then most open PRs (name tiebreak)."""
    return (
        -_gh_open_issues(plan),
        -_gh_open_prs(plan),
        plan.repo.full_name.lower(),
    )


def _fix_prefix(fix_id: str) -> str:
    head = (fix_id or "").split("-", 1)[0].upper()
    return head if head in _PREFIX_ORDER[:-1] else "OTHER"


def _top_categories(plan: RepoPlan, *, limit: int = 3) -> list[dict[str, Any]]:
    scores = plan.score.category_scores or {}
    ranked = sorted(scores.items(), key=lambda kv: (-float(kv[1]), kv[0]))
    return [{"name": name, "score": score} for name, score in ranked[:limit]]


def _hbar(items: list[tuple[str, int | float]], *, limit: int = 8) -> list[dict[str, Any]]:
    top = items[:limit]
    peak = max((float(v) for _, v in top), default=1.0) or 1.0
    return [
        {"label": label, "value": value, "pct": round(100.0 * float(value) / peak, 1)}
        for label, value in top
    ]


def _priority_spark(
    priority: list[RepoPlan], cards: list[dict[str, Any]]
) -> dict[str, Any]:
    n = min(len(priority), len(cards))
    if not n:
        return {"points": [], "line": "", "area": ""}
    pts: list[dict[str, Any]] = []
    for i in range(n):
        p, c = priority[i], cards[i]
        x = 0.0 if n == 1 else round(320.0 * i / (n - 1), 1)
        y = round(66.0 - (float(p.score.attention) / 100.0 * 56.0), 1)
        pts.append(
            {
                "label": p.repo.name[:22],
                "value": p.score.attention,
                "band": c["band"],
                "x": x,
                "y": y,
            }
        )
    line = "M " + " L ".join(f"{p['x']} {p['y']}" for p in pts)
    area = (
        f"M {pts[0]['x']} 66 L "
        + " L ".join(f"{p['x']} {p['y']}" for p in pts)
        + f" L {pts[-1]['x']} 66 Z"
    )
    return {"points": pts, "line": line, "area": area}


def _rubric_means(plans: list[RepoPlan]) -> list[dict[str, Any]]:
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for p in plans:
        for name, score in (p.score.category_scores or {}).items():
            key = str(name)
            sums[key] = sums.get(key, 0.0) + float(score)
            counts[key] = counts.get(key, 0) + 1
    rows = [
        (k, round(sums[k] / max(1, counts[k]), 1))
        for k in sums
    ]
    rows.sort(key=lambda kv: (-kv[1], kv[0]))
    return _hbar(rows, limit=10)


def _prefix_groups(fix_counts: dict[str, int]) -> list[dict[str, Any]]:
    buckets = {k: 0 for k in _PREFIX_ORDER}
    for fid, n in fix_counts.items():
        buckets[_fix_prefix(fid)] += int(n)
    total = sum(buckets.values()) or 1
    return [
        {
            "key": k,
            "label": k,
            "count": buckets[k],
            "pct": round(100.0 * buckets[k] / total, 1),
        }
        for k in _PREFIX_ORDER
        if buckets[k] or k != "OTHER"
    ]


def build_report_view(
    plans: list[RepoPlan],
    *,
    target_label: str,
    mode: str,
    report_banner: str | None = None,
    health_delta: dict[str, Any] | None = None,
    read_only: bool = False,
    pages_safe: bool = False,
    actions_unavailable: bool | None = None,
) -> dict[str, Any]:
    active = [p for p in plans if p.repo.status != RepoStatus.ARCHIVED]
    archived = [p for p in plans if p.repo.status == RepoStatus.ARCHIVED]
    att = [p.score.attention for p in plans]
    mean_att = round(sum(att) / len(att), 1) if att else 0.0
    max_att = max(att) if att else 0.0
    auto_n = sum(len(p.auto_fixes) for p in plans)
    agent_n = sum(len(p.agent_fixes) for p in plans)
    human_n = sum(len(p.human_fixes) for p in plans)
    open_fixes = auto_n + agent_n + human_n

    if actions_unavailable is None:
        env = (os.environ.get("ARGUS_ACTIONS_UNAVAILABLE") or "").strip().lower()
        actions_unavailable = env in ("1", "true", "yes", "on")

    fix_counts: dict[str, int] = {}
    lang_counts: dict[str, int] = {}
    band_counts = {"high": 0, "medium": 0, "good": 0}
    hist = [0, 0, 0, 0, 0]
    for p in plans:
        a = float(p.score.attention)
        hist[min(4, int(a // 20))] += 1
        open_any = bool(p.human_fixes or p.agent_fixes or p.auto_fixes)
        band_counts[_band(a, open_any)] += 1
        lang = str(_raw(p).get("language") or "Unknown")
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
        for m in (*p.human_fixes, *p.agent_fixes, *p.auto_fixes):
            fix_counts[m.fix.id] = fix_counts.get(m.fix.id, 0) + 1
    top_fixes = sorted(fix_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    hist_max = max(hist) if hist else 1

    # Full active fleet, Issues → PRs → attention. No Priority / omit split.
    fleet_plans = sorted(active, key=_urgency_key)
    healthy_omitted = 0
    priority = fleet_plans  # grandma + spark helpers over full fleet
    fleet_rows: list[dict[str, Any]] = []
    for p in fleet_plans:
        open_any = bool(p.human_fixes or p.agent_fixes or p.auto_fixes)
        band = _band(p.score.attention, open_any)
        open_n = _argus_open_count(p)
        gh_issues = _gh_open_issues(p)
        gh_prs = _gh_open_prs(p)
        fleet_rows.append(
            {
                "full_name": p.repo.full_name,
                "name": p.repo.name,
                "url": p.repo.html_url or f"https://github.com/{p.repo.full_name}",
                "status": p.repo.status.value,
                "band": band,
                "lang": str(_raw(p).get("language") or "—"),
                "attention": p.score.attention,
                "bar_width": max(8, min(100, int(p.score.attention))),
                "open_fixes": open_n,
                "issues": gh_issues,
                "prs": gh_prs,
                "gh_issues": gh_issues,
                "gh_prs": gh_prs,
            }
        )
    cards = fleet_rows[:12]  # sparkline sample; fleet table uses all rows

    assessment = [
        f"Portfolio size: {len(plans)} repositories "
        f"({len(active)} non-archived, {len(archived)} archived).",
        f"Mean attention {mean_att}/100 (max {max_att}); {open_fixes} open Argus fixes "
        f"({human_n} human-class).",
    ]
    if top_fixes:
        assessment.append(
            "Most common open fix ids: "
            + ", ".join(f"`{fid}`×{n}" for fid, n in top_fixes[:5])
            + "."
        )
    else:
        assessment.append("No open Argus fix matches — fleet looks clean on matched rules.")
    pr_total = sum(_gh_open_prs(p) for p in active)
    issue_total = sum(_gh_open_issues(p) for p in active)
    if pr_total or issue_total:
        assessment.append(
            f"GitHub surface: {issue_total} Issues + {pr_total} open PRs "
            "(PRs are never counted as Issues)."
        )
    if health_delta:
        assessment.append(
            f"This run health delta: open fixes "
            f"{(health_delta.get('totals_before') or {}).get('open_fixes')}→"
            f"{(health_delta.get('totals_after') or {}).get('open_fixes')} "
            f"(Δ {health_delta.get('delta_open_fixes')})."
        )
    if actions_unavailable:
        assessment.append(
            "GitHub Actions unavailable (free-tier / no paid minutes) — local path in use."
        )

    grandma: list[dict[str, Any]] = []
    if not pages_safe:
        for p in priority:
            if not p.human_fixes:
                continue
            m = p.human_fixes[0]
            grandma.append(
                {
                    "index": len(grandma) + 1,
                    "title": f"{m.fix.title} ({p.repo.name})",
                    "why": m.fix.why,
                    "steps": (m.fix.human_steps or "").strip(),
                    "gate": m.fix.gate or "Steps above are complete.",
                    "url": p.repo.html_url or f"https://github.com/{p.repo.full_name}",
                }
            )
            if len(grandma) >= 5:
                break

    band_total = sum(band_counts.values()) or 1
    fix_total = open_fixes or 1
    prefixes = _prefix_groups(fix_counts)
    rubric = _rubric_means(plans)
    return {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d"),
        "generated_at_iso": datetime.now(UTC).isoformat(),
        "target_label": target_label,
        "mode": mode,
        "read_only": read_only,
        "pages_safe": pages_safe,
        "actions_unavailable": bool(actions_unavailable),
        "report_banner": report_banner,
        "health_delta": health_delta,
        "stats": {
            "repos": len(plans),
            "active": len(active),
            "archived": len(archived),
            "open_fixes": open_fixes,
            "human_fixes": human_n,
            "auto_fixes": auto_n,
            "agent_fixes": agent_n,
            "mean_attention": mean_att,
            "max_attention": max_att,
        },
        "charts": {
            "attention_hist": [
                {
                    "label": lab,
                    "count": hist[i],
                    "pct": round(100.0 * hist[i] / hist_max, 1) if hist_max else 0,
                }
                for i, lab in enumerate(["0–20", "20–40", "40–60", "60–80", "80–100"])
            ],
            "bands": [
                {
                    "key": k,
                    "count": band_counts[k],
                    "pct": round(100.0 * band_counts[k] / band_total, 1),
                }
                for k in ("high", "medium", "good")
            ],
            "fix_classes": [
                {
                    "key": "auto",
                    "label": "Auto-safe",
                    "count": auto_n,
                    "pct": round(100.0 * auto_n / fix_total, 1),
                },
                {
                    "key": "agent",
                    "label": "Agent",
                    "count": agent_n,
                    "pct": round(100.0 * agent_n / fix_total, 1),
                },
                {
                    "key": "human",
                    "label": "Human",
                    "count": human_n,
                    "pct": round(100.0 * human_n / fix_total, 1),
                },
            ],
            "prefix_groups": prefixes,
            "rubric_means": rubric,
            "top_fixes": _hbar([(a, b) for a, b in top_fixes]),
            "languages": _hbar(
                sorted(lang_counts.items(), key=lambda kv: (-kv[1], kv[0])), limit=8
            ),
            "priority_attention": _priority_spark(priority[:12], cards),
            "fleet_attention": _priority_spark(priority[:12], cards),
        },
        "assessment_bullets": assessment,
        "healthy_omitted": healthy_omitted,
        "priority_cards": cards,  # compat alias = first 12 fleet rows
        "fleet": fleet_rows,
        "archived_cards": [
            {
                "name": p.repo.name,
                "full_name": p.repo.full_name,
                "url": p.repo.html_url or f"https://github.com/{p.repo.full_name}",
                "meta": _meta_line(p),
            }
            for p in archived
        ],
        "grandma_tasks": grandma,
        "strong": [
            "Argus covers mechanical hygiene via gated auto_safe + YOLO handlers.",
            "YOLO merges chore(argus) / Dependabot (all bump levels, CI green); never force-push.",
            "Full weakness detail stays private (argus-history); Pages stay sanitized.",
        ],
        "attention_blurb": (
            "Attention is a deterministic 0–100 “needs work” score from config/rubric.yaml. "
            "Fleet lists every active repo, sorted by Issues then open PRs. "
            "Issues and PRs stay in separate columns — GitHub’s open_issues_count wrongly "
            "includes PRs; Argus strips that. `argus explain owner/name` dumps one repo."
        ),
    }
