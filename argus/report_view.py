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
    issues = int(raw.get("open_issues_count") or 0)
    pushed = str(raw.get("pushed_at") or "")[:10] or "—"
    return f"{lang} · ★{stars} · License: {spdx} · {issues} open issues · Last push {pushed}"


def _band(attention: float, open_any: bool) -> str:
    """Badge band for UI. No open Argus fixes → always good (score still shown)."""
    if not open_any:
        return "good"
    if attention >= 55:
        return "high"
    if attention >= 35:
        return "medium"
    return "good"


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

    priority = sorted(active, key=lambda p: p.score.attention, reverse=True)
    cards = []
    for p in priority[:12]:
        open_any = bool(p.human_fixes or p.agent_fixes or p.auto_fixes)
        band = _band(p.score.attention, open_any)
        top_cats = _top_categories(p)
        open_n = len(p.auto_fixes) + len(p.agent_fixes) + len(p.human_fixes)
        card: dict[str, Any] = {
            "full_name": p.repo.full_name,
            "name": p.repo.name,
            "url": p.repo.html_url or f"https://github.com/{p.repo.full_name}",
            "status": p.repo.status.value,
            "band": band,
            "attention": p.score.attention,
            "meta": _meta_line(p),
            "top_categories": top_cats,
            "categories_line": " · ".join(
                f"{c['name']} {c['score']}" for c in top_cats
            ),
            "bar_width": max(8, min(95, int(p.score.attention))),
            "open_fixes": open_n,
            "description": (p.repo.description or "")[:220],
        }
        if pages_safe:
            card["issues"] = []
        else:
            card["issues"] = [
                f"`{m.fix.id}` — {m.fix.title}"
                for m in (*p.auto_fixes, *p.agent_fixes, *p.human_fixes)[:8]
            ]
        cards.append(card)

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
        },
        "assessment_bullets": assessment,
        "priority_cards": cards,
        "fleet": [
            {
                "name": p.repo.name,
                "url": p.repo.html_url or f"https://github.com/{p.repo.full_name}",
                "issues": int(_raw(p).get("open_issues_count") or 0),
                "lang": str(_raw(p).get("language") or "—"),
                "attention": p.score.attention,
                "open_fixes": len(p.auto_fixes) + len(p.agent_fixes) + len(p.human_fixes),
            }
            for p in priority[12:]
        ],
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
            "YOLO merges only chore(argus) / Dependabot patch PRs; never force-push.",
            "Full weakness detail stays private (argus-history); Pages stay sanitized.",
        ],
        "attention_blurb": (
            "Attention is a deterministic 0–100 “needs work” score: category rules "
            "(momentum, CI, deps, hygiene, security, PRs, …) from live GitHub signals, "
            "blended by weights in config/rubric.yaml. Higher means more portfolio care. "
            "Badge bands follow open Argus fixes (empty → good). Dump one repo with "
            "`argus explain owner/name`."
        ),
    }
