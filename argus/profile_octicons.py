"""Self-hosted Primer Octicons (colored fills) for Overview stats."""

from __future__ import annotations

import re

from argus.paths import TEMPLATES_DIR

# Mid-bright fills readable on GitHub light and dark README canvases.
_FILLS = {
    "star-16": "#e3b341",
    "eye-16": "#8b949e",
    "repo-forked-16": "#3fb950",
    "pulse-16": "#58a6ff",
}


def octicon_rel_path(name: str) -> str:
    return f"./assets/octicons/{name}.svg"


def default_octicon_urls() -> dict[str, str]:
    return {
        "octicon_star": octicon_rel_path("star-16"),
        "octicon_watch": octicon_rel_path("eye-16"),
        "octicon_fork": octicon_rel_path("repo-forked-16"),
        "octicon_views": octicon_rel_path("pulse-16"),
    }


def _with_fill(svg: str, fill: str) -> str:
    if re.search(r"<path[^>]*\bfill=", svg):
        return re.sub(r'(<path[^>]*\bfill=")[^"]*"', rf'\1{fill}"', svg, count=1)
    return svg.replace("<path ", f'<path fill="{fill}" ', 1)


def load_octicon_svgs() -> dict[str, str]:
    """Path under profile repo → SVG text with metric-colored fill."""
    base = TEMPLATES_DIR / "octicons"
    out: dict[str, str] = {}
    for name, fill in _FILLS.items():
        path = base / f"{name}.svg"
        if not path.exists():
            continue
        out[f"assets/octicons/{name}.svg"] = _with_fill(path.read_text(encoding="utf-8"), fill)
    return out
