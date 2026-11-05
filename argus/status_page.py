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


def safe_status_payload(plans: list[RepoPlan]) -> dict[str, Any]:
    human = sum(len(p.human_fixes) for p in plans)
    return {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "repo_count": len(plans),
        "human_open": human,
        "ok": "needs you" if human else "quiet",
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
    )


def write_status_artifacts(plans: list[RepoPlan], dist_dir: Path | None = None) -> Path:
    """Write public-safe status.html + status.json (no per-repo security fields)."""
    ensure_runtime_dirs()
    out = dist_dir or DIST_DIR
    out.mkdir(parents=True, exist_ok=True)
    html = compose_status_html(plans)
    path = out / "status.html"
    path.write_text(html, encoding="utf-8")
    (out / "status.json").write_text(
        json.dumps(safe_status_payload(plans), indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def is_security_fix(fix_id: str) -> bool:
    return fix_id.upper().startswith("SEC-")
