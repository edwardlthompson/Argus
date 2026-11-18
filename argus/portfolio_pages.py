"""Sanitized public Pages portfolio dashboard (no per-repo finding titles)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from argus.models import RepoPlan
from argus.paths import DIST_DIR, TEMPLATES_DIR, ensure_runtime_dirs
from argus.report_view import build_report_view


def compose_portfolio_pages_html(
    plans: list[RepoPlan],
    *,
    health_delta: dict[str, Any] | None = None,
    target_label: str = "portfolio",
    mode: str = "run",
) -> str:
    view = build_report_view(
        plans,
        target_label=target_label,
        mode=mode,
        health_delta=health_delta,
        pages_safe=True,
        report_banner=(
            "Public dashboard — metrics only. Per-repo security findings are never listed here."
        ),
    )
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template("portfolio_pages.html.j2").render(view=view)


def write_portfolio_pages(
    plans: list[RepoPlan],
    *,
    health_delta: dict[str, Any] | None = None,
    dist_dir: Path | None = None,
    target_label: str = "portfolio",
    mode: str = "run",
) -> dict[str, Path]:
    ensure_runtime_dirs()
    out = dist_dir or DIST_DIR
    out.mkdir(parents=True, exist_ok=True)
    view = build_report_view(
        plans,
        target_label=target_label,
        mode=mode,
        health_delta=health_delta,
        pages_safe=True,
    )
    html = compose_portfolio_pages_html(
        plans,
        health_delta=health_delta,
        target_label=target_label,
        mode=mode,
    )
    html_path = out / "portfolio-pages.html"
    json_path = out / "portfolio-pages.json"
    html_path.write_text(html, encoding="utf-8")
    payload = {
        "generated_at": view.get("generated_at_iso"),
        "pages_safe": True,
        "stats": view.get("stats"),
        "charts": {
            "bands": (view.get("charts") or {}).get("bands"),
            "fix_classes": (view.get("charts") or {}).get("fix_classes"),
            "prefix_groups": (view.get("charts") or {}).get("prefix_groups"),
            "top_fixes": (view.get("charts") or {}).get("top_fixes"),
            "rubric_means": (view.get("charts") or {}).get("rubric_means"),
        },
        "actions_unavailable": view.get("actions_unavailable"),
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {"portfolio_pages": html_path, "portfolio_pages_json": json_path}
