"""Generate a self-hosted profile Overview banner SVG (no remote widgets)."""

from __future__ import annotations

import html

_BANNER_STYLE = """
<style>
@keyframes pulseGlow { 0%,100% { opacity:.55 } 50% { opacity:1 } }
@keyframes barShimmer {
  0% { transform: translateX(-40%) }
  100% { transform: translateX(140%) }
}
@keyframes nameBreathe { 0%,100% { opacity:.92 } 50% { opacity:1 } }
.glow { animation: pulseGlow 9s ease-in-out infinite }
.bar-shine {
  animation: barShimmer 10s linear infinite;
}
.name { animation: nameBreathe 8s ease-in-out infinite }
</style>
"""


def render_banner_svg(display_name: str, tagline: str = "") -> str:
    """Richer portfolio hero with subtle CSS motion; may be replaced by operator."""
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
{_BANNER_STYLE}
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
<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
<stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
<stop offset="50%" stop-color="#ffffff" stop-opacity="0.45"/>
<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
</linearGradient>
<clipPath id="barClip"><rect x="390" y="196" width="420" height="5" rx="2.5"/></clipPath>
</defs>
<rect width="1200" height="240" fill="url(#g)"/>
<path class="glow" d="M0 180 C 200 140, 400 210, 600 170 S 1000 120, 1200 160 L 1200 240 L 0 240 Z" fill="url(#glow)"/>
<circle class="glow" cx="1080" cy="36" r="130" fill="#38bdf8" fill-opacity="0.14"/>
<circle class="glow" cx="1040" cy="70" r="54" fill="#2dd4bf" fill-opacity="0.16"/>
<circle class="glow" cx="90" cy="200" r="100" fill="#2dd4bf" fill-opacity="0.12"/>
<path d="M40 48 H 160 M40 58 H 120" stroke="#38bdf8" stroke-opacity="0.35" stroke-width="2"/>
<path d="M1040 190 H 1160 M1080 200 H 1160" stroke="#2dd4bf" stroke-opacity="0.35" stroke-width="2"/>
<rect x="390" y="196" width="420" height="5" rx="2.5" fill="url(#bar)"/>
<g clip-path="url(#barClip)">
<rect class="bar-shine" x="390" y="196" width="120" height="5" fill="url(#shine)"/>
</g>
<text class="name" x="600" y="{name_y}" text-anchor="middle" fill="#f8fafc"
 font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="54" font-weight="700">{name}</text>
{subtitle}
</svg>
"""


def render_divider_svg() -> str:
    """Thin accent bar with slow sliding highlight for Featured / Tech stack."""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="12" viewBox="0 0 1200 12">
<style>
@keyframes slide {
  0% { transform: translateX(-30%) }
  100% { transform: translateX(130%) }
}
.shine { animation: slide 9s linear infinite }
</style>
<defs>
<linearGradient id="d" x1="0" y1="0" x2="1" y2="0">
<stop offset="0%" stop-color="#0ea5e9" stop-opacity="0.15"/>
<stop offset="50%" stop-color="#22d3ee" stop-opacity="0.85"/>
<stop offset="100%" stop-color="#14b8a6" stop-opacity="0.15"/>
</linearGradient>
<linearGradient id="s" x1="0" y1="0" x2="1" y2="0">
<stop offset="0%" stop-color="#fff" stop-opacity="0"/>
<stop offset="50%" stop-color="#fff" stop-opacity="0.55"/>
<stop offset="100%" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<clipPath id="c"><rect x="40" y="4" width="1120" height="4" rx="2"/></clipPath>
</defs>
<rect x="40" y="4" width="1120" height="4" rx="2" fill="url(#d)"/>
<g clip-path="url(#c)">
<rect class="shine" x="40" y="4" width="180" height="4" fill="url(#s)"/>
</g>
</svg>
"""
