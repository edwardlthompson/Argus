"""Self-hosted Primer Octicons (muted fill) for Overview stats."""

from __future__ import annotations

from argus.paths import TEMPLATES_DIR

_FILL = "#8b949e"
_NAMES = ("star-16", "eye-16", "repo-forked-16", "pulse-16")


def octicon_rel_path(name: str) -> str:
    return f"./assets/octicons/{name}.svg"


def default_octicon_urls() -> dict[str, str]:
    return {
        "octicon_star": octicon_rel_path("star-16"),
        "octicon_watch": octicon_rel_path("eye-16"),
        "octicon_fork": octicon_rel_path("repo-forked-16"),
        "octicon_views": octicon_rel_path("pulse-16"),
    }


def load_octicon_svgs() -> dict[str, str]:
    """Path under profile repo → SVG text with muted fill."""
    base = TEMPLATES_DIR / "octicons"
    out: dict[str, str] = {}
    for name in _NAMES:
        path = base / f"{name}.svg"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if f'fill="{_FILL}"' not in text and "<path " in text:
            text = text.replace("<path ", f'<path fill="{_FILL}" ', 1)
        out[f"assets/octicons/{name}.svg"] = text
    return out
