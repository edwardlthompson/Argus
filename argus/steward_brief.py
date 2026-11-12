"""Private Tuesday Steward visual brief (never publish to public Pages)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from argus.models import RepoPlan
from argus.paths import DIST_DIR, TEMPLATES_DIR, ensure_runtime_dirs
from argus.report_view import build_report_view


def compose_steward_brief_html(
    plans: list[RepoPlan],
    *,
    health_delta: dict[str, Any] | None = None,
    hotspots: dict[str, Any] | None = None,
    target_label: str = "portfolio",
    mode: str = "run",
    pages_url: str | None = None,
    history_hint: str | None = None,
) -> str:
    view = build_report_view(
        plans,
        target_label=target_label,
        mode=mode,
        health_delta=health_delta,
        pages_safe=False,
    )
    hs = hotspots or {}
    before = hs.get("before") if isinstance(hs.get("before"), dict) else None
    hotspot_rows = list(
        ((before or {}).get("by_fix_id") if before else None)
        or hs.get("by_fix_id")
        or []
    )
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template("steward_brief.html.j2").render(
        view=view,
        hotspot_rows=hotspot_rows,
        pages_url=pages_url or "",
        history_hint=history_hint
        or "Private: argus-history/reports/latest-steward.html on the runner",
    )


def write_steward_brief(
    plans: list[RepoPlan],
    *,
    health_delta: dict[str, Any] | None = None,
    hotspots: dict[str, Any] | None = None,
    dist_dir: Path | None = None,
    target_label: str = "portfolio",
    mode: str = "run",
    pages_url: str | None = None,
) -> Path:
    ensure_runtime_dirs()
    out = dist_dir or DIST_DIR
    out.mkdir(parents=True, exist_ok=True)
    html = compose_steward_brief_html(
        plans,
        health_delta=health_delta,
        hotspots=hotspots,
        target_label=target_label,
        mode=mode,
        pages_url=pages_url,
    )
    path = out / "steward-brief.html"
    path.write_text(html, encoding="utf-8")
    return path
