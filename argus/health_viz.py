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


def _bar(x: float, y: float, w: float, h: float, fill: str, label: str = "") -> str:
    esc = label.replace("&", "&amp;").replace("<", "&lt;")
    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(0.0, w):.1f}" height="{h:.1f}" '
        f'rx="3" fill="{fill}"/>'
    ]
    if esc:
        parts.append(
            f'<text x="{x + 4:.1f}" y="{y + h - 6:.1f}" font-size="11" '
            f'font-family="Segoe UI,system-ui,sans-serif" fill="#1a1a1a">{esc}</text>'
        )
    return "".join(parts)


def compose_infographic_svg(
    before: dict[str, Any],
    after: dict[str, Any],
    delta: dict[str, Any],
    hotspots: dict[str, Any] | None = None,
) -> str:
    """Self-contained SVG: before/after totals + top problem fix ids."""
    bt = before.get("totals") or {}
    at = after.get("totals") or {}
    hotspots = hotspots or hotspots_from_snapshot(before)
    max_open = max(
        float(bt.get("open_fixes") or 0),
        float(at.get("open_fixes") or 0),
        1.0,
    )
    scale = 220.0 / max_open
    bw = float(bt.get("open_fixes") or 0) * scale
    aw = float(at.get("open_fixes") or 0) * scale
    rows = hotspots.get("by_fix_id") or []
    max_fix = max((int(r.get("count") or 0) for r in rows), default=1) or 1
    height = 220 + max(0, len(rows)) * 22
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" '
        f'viewBox="0 0 720 {height}">',
        '<rect width="100%" height="100%" fill="#f4f6f8"/>',
        '<text x="24" y="32" font-size="18" font-weight="700" '
        'font-family="Segoe UI,system-ui,sans-serif" fill="#111">Argus scan — before / after</text>',
        f'<text x="24" y="52" font-size="12" font-family="Segoe UI,system-ui,sans-serif" fill="#444">'
        f'Δ open fixes {delta.get("delta_open_fixes", 0)} · '
        f'Δ mean attention {delta.get("delta_mean_attention", 0)}</text>',
        '<text x="24" y="88" font-size="13" font-weight="600" '
        'font-family="Segoe UI,system-ui,sans-serif" fill="#333">Open fixes</text>',
        _bar(24, 98, bw, 28, "#c45c26", f"Before {bt.get('open_fixes', 0)}"),
        _bar(24, 134, aw, 28, "#2f6f4e", f"After {at.get('open_fixes', 0)}"),
        '<text x="24" y="190" font-size="13" font-weight="600" '
        'font-family="Segoe UI,system-ui,sans-serif" fill="#333">'
        "Hottest problem types (before)</text>",
    ]
    y = 204
    for row in rows[:12]:
        fid = str(row.get("id") or "?")
        cnt = int(row.get("count") or 0)
        w = 400.0 * (cnt / max_fix)
        parts.append(_bar(24, y, w, 16, "#5b7c99", f"{fid} ×{cnt}"))
        y += 22
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
        f"<li><code>{r.get('repo')}</code> — open {r.get('open_fixes')} · "
        f"attention {r.get('attention')}</li>"
        for r in repos[:15]
    )
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\"/>"
        "<title>Argus health infographic</title>"
        "<style>body{font-family:Segoe UI,system-ui,sans-serif;margin:1.5rem;"
        "background:#f4f6f8;color:#111} code{font-size:.9em}</style></head><body>"
        "<h1>Argus portfolio scan</h1>"
        f"{svg}"
        "<h2>Repos causing the most problems</h2>"
        f"<ol>{lis or '<li>None</li>'}</ol>"
        "<p>Generated deterministically from health snapshots — not by Grok.</p>"
        "</body></html>\n"
    )
