"""Generate a minimal profile Overview banner SVG (no external assets)."""

from __future__ import annotations

import html


def render_banner_svg(display_name: str, tagline: str = "") -> str:
    """Portfolio banner with name + tagline; operator may replace the file later."""
    name = html.escape((display_name or "GitHub").strip()[:80])
    line = html.escape((tagline or "").strip()[:120])
    subtitle = (
        f'<text x="600" y="155" text-anchor="middle" fill="#94a3b8" '
        f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="22">{line}</text>'
        if line
        else ""
    )
    name_y = "118" if line else "130"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="240" viewBox="0 0 1200 240">'
        "<defs>"
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="#0b1220"/>'
        '<stop offset="55%" stop-color="#12263f"/>'
        '<stop offset="100%" stop-color="#0f766e"/>'
        "</linearGradient>"
        '<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="#38bdf8"/>'
        '<stop offset="100%" stop-color="#2dd4bf"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="1200" height="240" fill="url(#g)"/>'
        '<circle cx="1080" cy="40" r="120" fill="#38bdf8" fill-opacity="0.08"/>'
        '<circle cx="80" cy="210" r="90" fill="#2dd4bf" fill-opacity="0.08"/>'
        '<rect x="420" y="198" width="360" height="4" rx="2" fill="url(#bar)"/>'
        f'<text x="600" y="{name_y}" text-anchor="middle" fill="#f8fafc" '
        f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="52" font-weight="700">'
        f"{name}</text>"
        f"{subtitle}"
        "</svg>\n"
    )
