"""Public status page — counts only, never per-repo security detail."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from argus.config_loader import load_yaml
from argus.models import RepoPlan
from argus.paths import CONFIG_DIR, DIST_DIR, TEMPLATES_DIR, ensure_runtime_dirs


def _inbox_cfg() -> dict[str, Any]:
    path = CONFIG_DIR / "inbox.yaml"
    if not path.exists():
        return {"controller_repo": "edwardlthompson/Argus"}
    return load_yaml(path)


def safe_status_payload(plans: list[RepoPlan], *, circuit_open: bool = False) -> dict[str, Any]:
    human = sum(len(p.human_fixes) for p in plans)
    return {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "repo_count": len(plans),
        "human_open": human,
        "ok": "needs you" if human else "quiet",
        "circuit_open": circuit_open,
    }


def compose_status_html(plans: list[RepoPlan]) -> str:
    payload = safe_status_payload(plans)
    cfg = _inbox_cfg()
    controller = str(cfg.get("controller_repo") or "edwardlthompson/Argus")
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template("status.html.j2").render(
        **payload,
        controller_url=f"https://github.com/{controller}",
        notify_rows=_recent_notify_rows(),
    )


def compose_badge_svg(plans: list[RepoPlan]) -> str:
    payload = safe_status_payload(plans)
    label = "argus"
    message = "needs you" if payload["human_open"] else "quiet"
    color = "#c97800" if payload["human_open"] else "#0f6b5c"
    # Simple shields-like SVG (counts only — no repo names)
    msg_w = 70 if payload["human_open"] else 48
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{70 + msg_w}" height="20" role="img" '
        f'aria-label="{label}: {message}">'
        f'<title>{label}: {message}</title>'
        f'<linearGradient id="s" x2="0" y2="100%">'
        f'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        f'<stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<rect rx="3" width="{70 + msg_w}" height="20" fill="#555"/>'
        f'<rect rx="3" x="70" width="{msg_w}" height="20" fill="{color}"/>'
        f'<path fill="{color}" d="M70 0h4v20h-4z"/>'
        f'<rect rx="3" width="{70 + msg_w}" height="20" fill="url(#s)"/>'
        f'<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">'
        f'<text x="35" y="15" fill="#010101" fill-opacity=".3">{label}</text>'
        f'<text x="35" y="14">{label}</text>'
        f'<text x="{70 + msg_w / 2}" y="15" fill="#010101" fill-opacity=".3">{message}</text>'
        f'<text x="{70 + msg_w / 2}" y="14">{message}</text></g></svg>\n'
    )


def _recent_notify_rows(limit: int = 5) -> list[dict[str, Any]]:
    from argus.paths import DATA_DIR

    path = DATA_DIR / "notifications.json"
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    rows = []
    for item in raw[-limit:]:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "ts": item.get("ts"),
                "human_count": item.get("human_count"),
                "channels": item.get("channels") or [],
            }
        )
    return rows


def write_status_artifacts(plans: list[RepoPlan], dist_dir: Path | None = None) -> Path:
    """Write public-safe status.html + status.json + badge (no per-repo security fields)."""
    ensure_runtime_dirs()
    out = dist_dir or DIST_DIR
    out.mkdir(parents=True, exist_ok=True)
    payload = safe_status_payload(plans)
    notify_rows = _recent_notify_rows()
    cfg = _inbox_cfg()
    controller = str(cfg.get("controller_repo") or "edwardlthompson/Argus")
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    html = env.get_template("status.html.j2").render(
        **payload,
        controller_url=f"https://github.com/{controller}",
        notify_rows=notify_rows,
    )
    path = out / "status.html"
    path.write_text(html, encoding="utf-8")
    (out / "status.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out / "badge.svg").write_text(compose_badge_svg(plans), encoding="utf-8")
    return path


def is_security_fix(fix_id: str) -> bool:
    return fix_id.upper().startswith("SEC-")
