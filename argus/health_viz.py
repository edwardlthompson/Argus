"""Deterministic before/after health infographic + problem hotspots (no LLM)."""

from __future__ import annotations

from collections import Counter
from typing import Any


def hotspots_from_snapshot(snap: dict[str, Any], *, top_n: int = 12) -> dict[str, Any]:
    """Aggregate which fix ids / repos drive open findings."""
    fix_counts: Counter[str] = Counter()
    repo_open: list[tuple[str, int, float]] = []
    for row in snap.get("repos") or []:
        fixes = list(row.get("auto") or []) + list(row.get("agent") or []) + list(
            row.get("human") or []
        )
        for fid in fixes:
            fix_counts[str(fid)] += 1
        open_n = len(fixes)
        if open_n:
            repo_open.append(
                (str(row.get("repo") or "?"), open_n, float(row.get("attention") or 0))
            )
    repo_open.sort(key=lambda t: (-t[1], -t[2], t[0]))
    return {
        "by_fix_id": [
            {"id": k, "count": v} for k, v in fix_counts.most_common(top_n)
        ],
        "by_repo": [
            {"repo": r, "open_fixes": n, "attention": a}
            for r, n, a in repo_open[:top_n]
        ],
    }


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _bar(
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    label: str = "",
    *,
    track_w: float = 0.0,
    text_color: str = "#e8eef7",
) -> str:
    esc = _esc(label)
    parts: list[str] = []
    if track_w > 0:
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{track_w:.1f}" height="{h:.1f}" '
            f'rx="5" fill="#0a101a" stroke="#243247" stroke-width="1"/>'
        )
    parts.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(0.0, w):.1f}" height="{h:.1f}" '
        f'rx="5" fill="{fill}"/>'
    )
    if esc:
        parts.append(
            f'<text x="{x + 10:.1f}" y="{y + h - 7:.1f}" font-size="11.5" font-weight="600" '
            f'font-family="Segoe UI,system-ui,sans-serif" fill="{text_color}">{esc}</text>'
        )
    return "".join(parts)


def _kpi_card(x: float, y: float, w: float, h: float, value: str, label: str, accent: str) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="8" fill="#132033" stroke="#243247" stroke-width="1"/>'
        f'<rect x="{x:.1f}" y="{y:.1f}" width="3.5" height="{h:.1f}" rx="2" fill="{accent}"/>'
        f'<text x="{x + 14:.1f}" y="{y + 27:.1f}" font-size="20" font-weight="700" '
        f'font-family="Segoe UI,system-ui,sans-serif" fill="#e8eef7">{_esc(value)}</text>'
        f'<text x="{x + 14:.1f}" y="{y + 45:.1f}" font-size="11" '
        f'font-family="Segoe UI,system-ui,sans-serif" fill="#8fa0b8">{_esc(label)}</text>'
    )


def compose_infographic_svg(
    before: dict[str, Any],
    after: dict[str, Any],
    delta: dict[str, Any],
    hotspots: dict[str, Any] | None = None,
) -> str:
    """Self-contained dark-themed SVG: operational KPIs + before/after + hotspots."""
    bt = before.get("totals") or {}
    at = after.get("totals") or {}
    hotspots = hotspots or hotspots_from_snapshot(before)

    repo_count = int(after.get("repo_count") or before.get("repo_count") or len(after.get("repos") or []))
    open_issues = int(at.get("open_issues") or 0)
    open_prs = int(at.get("open_prs") or 0)
    open_fixes_after = int(at.get("open_fixes") or 0)
    open_fixes_before = int(bt.get("open_fixes") or 0)
    ci_pct = at.get("ci_pass_pct")
    ci_label = f"{ci_pct:.0f}%" if isinstance(ci_pct, (int, float)) else "—"
    ci_accent = "#3dd68c" if (isinstance(ci_pct, (int, float)) and ci_pct >= 85) else "#e6b84d"

    max_open = max(float(open_fixes_before), float(open_fixes_after), 1.0)
    track_w = 672.0
    bw = (float(open_fixes_before) / max_open) * track_w if open_fixes_before else 0.0
    aw = (float(open_fixes_after) / max_open) * track_w if open_fixes_after else 0.0

    rows = hotspots.get("by_fix_id") or []
    max_fix = max((int(r.get("count") or 0) for r in rows), default=1) or 1
    hotspot_h = max(1, min(10, len(rows))) * 26 if rows else 28
    height = 285 + hotspot_h

    cards = [
        (str(repo_count), "Active Repos", "#4aa3f0"),
        (ci_label, "CI Passing", ci_accent),
        (str(open_issues), "Open Issues", "#f07178" if open_issues else "#3dd68c"),
        (str(open_prs), "Open PRs", "#4aa3f0" if open_prs else "#3dd68c"),
        (str(open_fixes_after), "Open Fixes", "#e6b84d" if open_fixes_after else "#3dd68c"),
    ]
    card_w = 126.0
    gap = 10.5
    kpi_svg = "".join(
        _kpi_card(24 + i * (card_w + gap), 66, card_w, 56, val, lab, acc)
        for i, (val, lab, acc) in enumerate(cards)
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" '
        f'viewBox="0 0 720 {height}">',
        "<defs>",
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#132033"/><stop offset="100%" stop-color="#0b1220"/>'
        "</linearGradient>",
        "</defs>",
        '<rect width="100%" height="100%" rx="10" fill="url(#bg)"/>',
        '<text x="24" y="34" font-size="18" font-weight="700" '
        'font-family="Segoe UI,system-ui,sans-serif" fill="#e8eef7">'
        "Argus Portfolio Health</text>",
        f'<text x="24" y="53" font-size="11.5" font-family="Segoe UI,system-ui,sans-serif" fill="#8fa0b8">'
        f'Δ open fixes {delta.get("delta_open_fixes", 0)} · '
        f'Issues {open_issues} · PRs {open_prs} · CI {ci_label}</text>',
        kpi_svg,
        '<text x="24" y="148" font-size="12.5" font-weight="600" '
        'font-family="Segoe UI,system-ui,sans-serif" fill="#8fa0b8">OPEN FIXES (BEFORE / AFTER)</text>',
        _bar(24, 158, bw, 26, "#d97745", f"Before · {open_fixes_before}", track_w=track_w),
        _bar(24, 192, aw, 26, "#2f9e6b", f"After · {open_fixes_after}", track_w=track_w),
        '<text x="24" y="246" font-size="12.5" font-weight="600" '
        'font-family="Segoe UI,system-ui,sans-serif" fill="#8fa0b8">'
        "TOP OPEN FIX TYPES</text>",
    ]
    y = 258
    if rows:
        for row in rows[:10]:
            fid = str(row.get("id") or "?")
            cnt = int(row.get("count") or 0)
            w = max(90.0, track_w * (cnt / max_fix))
            parts.append(_bar(24, y, w, 20, "#3b76a8", f"{fid} ×{cnt}", track_w=track_w))
            y += 26
    else:
        parts.append(
            f'<text x="24" y="{y + 14}" font-size="12" font-family="Segoe UI,system-ui,sans-serif" '
            'fill="#3dd68c">All clear — 0 open fixes across the portfolio.</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def compose_infographic_html(
    before: dict[str, Any],
    after: dict[str, Any],
    delta: dict[str, Any],
    hotspots: dict[str, Any] | None = None,
) -> str:
    svg = compose_infographic_svg(before, after, delta, hotspots)
    hotspots = hotspots or hotspots_from_snapshot(before)
    repos = hotspots.get("by_repo") or []
    lis = "".join(
        f"<li><code>{_esc(str(r.get('repo') or '?'))}</code> — "
        f"{int(r.get('open_fixes') or 0)} open fix(es)</li>"
        for r in repos[:15]
    )
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>'
        "<title>Argus health infographic</title>"
        "<style>body{font-family:Segoe UI,system-ui,sans-serif;margin:1.75rem auto;max-width:760px;"
        "padding:0 1rem;background:#0b1220;color:#e8eef7}code{font-size:.9em;color:#4aa3f0}"
        "h1,h2{font-weight:650}p,li{color:#8fa0b8}</style></head><body>"
        "<h1>Argus Portfolio Health</h1>"
        f"{svg}"
        "<h2>Repos with open fixes</h2>"
        f"<ol>{lis or '<li>All clear — 0 repos with open fixes.</li>'}</ol>"
        "<p>Generated deterministically from health snapshots.</p>"
        "</body></html>\n"
    )
