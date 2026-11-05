"""Generate a self-hosted profile Overview banner SVG (no remote widgets)."""

from __future__ import annotations

import html


def render_banner_svg(display_name: str, tagline: str = "") -> str:
    """Richer portfolio hero; operator may replace assets/argus-banner.svg later."""
    name = html.escape((display_name or "GitHub").strip()[:80])
    line = html.escape((tagline or "").strip()[:120])
    subtitle = (
        f'<text x="600" y="152" text-anchor="middle" fill="#94a3b8" '
        f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="22">{line}</text>'
        if line
        else ""
    )
    name_y = "112" if line else "128"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="240" viewBox="0 0 1200 240">
<defs>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0%" stop-color="#070b14"/>
<stop offset="45%" stop-color="#0f2744"/>
<stop offset="100%" stop-color="#0f766e"/>
</linearGradient>
<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
<stop offset="0%" stop-color="#38bdf8"/>
<stop offset="50%" stop-color="#22d3ee"/>
<stop offset="100%" stop-color="#2dd4bf"/>
</linearGradient>
<linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="#38bdf8" stop-opacity="0.25"/>
<stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/>
</linearGradient>
</defs>
<rect width="1200" height="240" fill="url(#g)"/>
<path d="M0 180 C 200 140, 400 210, 600 170 S 1000 120, 1200 160 L 1200 240 L 0 240 Z" fill="url(#glow)"/>
<circle cx="1080" cy="36" r="130" fill="#38bdf8" fill-opacity="0.10"/>
<circle cx="1040" cy="70" r="54" fill="#2dd4bf" fill-opacity="0.12"/>
<circle cx="90" cy="200" r="100" fill="#2dd4bf" fill-opacity="0.10"/>
<path d="M40 48 H 160 M40 58 H 120" stroke="#38bdf8" stroke-opacity="0.35" stroke-width="2"/>
<path d="M1040 190 H 1160 M1080 200 H 1160" stroke="#2dd4bf" stroke-opacity="0.35" stroke-width="2"/>
<rect x="390" y="196" width="420" height="5" rx="2.5" fill="url(#bar)"/>
<text x="600" y="{name_y}" text-anchor="middle" fill="#f8fafc"
 font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="54" font-weight="700">{name}</text>
{subtitle}
</svg>
"""
