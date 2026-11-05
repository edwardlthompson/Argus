"""Compose GitHub profile Overview README from live user + portfolio data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from argus.config_loader import load_yaml
from argus.models import RepoPlan
from argus.paths import CONFIG_DIR, TEMPLATES_DIR

MARKER = "<!-- argus:profile-readme -->"


def load_profile_readme_config(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "profile_readme.yaml")
    if not path.exists():
        return {"enabled": False}
    data = load_yaml(path)
    return data if isinstance(data, dict) else {"enabled": False}


def _lang_counts(plans: list[RepoPlan]) -> list[str]:
    # Prefer topics + repo names as a stand-in until language API is wired per-repo.
    counts: dict[str, int] = {}
    for plan in plans:
        if plan.repo.private or plan.repo.archived or plan.repo.fork:
            continue
        if plan.repo.owner == plan.repo.name:
            continue
        for t in plan.repo.topics:
            key = t.strip()
            if len(key) < 2:
                continue
            counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [k for k, _ in ranked]


def _featured(plans: list[RepoPlan], limit: int) -> list[dict[str, str]]:
    cands = [
        p
        for p in plans
        if not p.repo.private and not p.repo.archived and not p.repo.fork and p.repo.owner != p.repo.name
    ]
    cands.sort(key=lambda p: (-p.score.attention, p.repo.name.lower()))
    out = []
    for p in cands[:limit]:
        out.append(
            {
                "name": p.repo.full_name,
                "html_url": p.repo.html_url or f"https://github.com/{p.repo.full_name}",
                "description": (p.repo.description or "")[:160],
            }
        )
    return out


def compose_profile_readme(
    *,
    user: dict[str, Any],
    plans: list[RepoPlan],
    config: dict[str, Any] | None = None,
) -> str:
    cfg = config or load_profile_readme_config()
    max_lang = int(cfg.get("max_languages") or 8)
    max_feat = int(cfg.get("max_featured_repos") or 6)
    languages = _lang_counts(plans)[:max_lang]
    # Prefer GitHub language field if present on user payload extensions later
    featured = _featured(plans, max_feat)
    topics = []
    seen = set()
    for plan in plans:
        for t in plan.repo.topics:
            if t not in seen and plan.repo.owner != plan.repo.name:
                seen.add(t)
                topics.append(t)
            if len(topics) >= 12:
                break
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
    )
    template = env.get_template("profile_readme.md.j2")
    login = str(user.get("login") or "")
    return template.render(
        display_name=user.get("name") or login or "GitHub user",
        tagline=cfg.get("tagline") or "",
        about=(cfg.get("about") or "").strip(),
        bio=(user.get("bio") or "").strip(),
        location=user.get("location") or "",
        blog=user.get("blog") or "",
        twitter=user.get("twitter_username") or "",
        roles=list(cfg.get("roles") or []),
        capabilities=list(cfg.get("capabilities") or []),
        principles=(cfg.get("principles") or "").strip(),
        open_to=(cfg.get("open_to") or "").strip(),
        languages=languages,
        topics=topics[:12],
        featured=featured,
        suggested_pins=[f["name"].split("/")[-1] for f in featured[:4]],
    )


def needs_profile_update(existing: str | None, new_body: str) -> bool:
    if not existing:
        return True
    if MARKER not in existing:
        return True
    # Compare without trailing whitespace drift
    return existing.strip() != new_body.strip()
