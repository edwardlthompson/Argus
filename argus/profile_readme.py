"""Compose GitHub profile Overview README from live user + portfolio data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from argus.config_loader import load_yaml
from argus.models import RepoPlan
from argus.paths import CONFIG_DIR, TEMPLATES_DIR
from argus.profile_featured import select_featured
from argus.profile_skills import (
    auto_about,
    bio_is_distinct,
    resolve_roles_and_capabilities,
)
from argus.profile_stack import ranked_languages

MARKER = "<!-- argus:profile-readme -->"


def load_profile_readme_config(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "profile_readme.yaml")
    if not path.exists():
        return {"enabled": False}
    data = load_yaml(path)
    return data if isinstance(data, dict) else {"enabled": False}


def _language_totals(plans: list[RepoPlan]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for plan in plans:
        langs = (plan.repo.raw or {}).get("argus_languages") or {}
        if isinstance(langs, dict):
            for name, nbytes in langs.items():
                totals[str(name)] = totals.get(str(name), 0) + int(nbytes)
    return totals


def compose_profile_readme(
    *,
    user: dict[str, Any],
    plans: list[RepoPlan],
    config: dict[str, Any] | None = None,
) -> str:
    cfg = config or load_profile_readme_config()
    max_lang = int(cfg.get("max_languages") or 8)
    max_feat = int(cfg.get("max_featured_repos") or 6)
    lang_rows = ranked_languages(_language_totals(plans), limit=max_lang)
    featured = select_featured(plans, max_feat)
    roles, capabilities, used_auto = resolve_roles_and_capabilities(plans, cfg)
    about = (cfg.get("about") or "").strip()
    if not about:
        about = auto_about(
            [r["name"] for r in lang_rows],
            [f["short"] for f in featured],
        )
    bio = (user.get("bio") or "").strip()
    show_bio = bio_is_distinct(about, bio)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("profile_readme.md.j2")
    login = str(user.get("login") or "")
    return template.render(
        display_name=user.get("name") or login or "GitHub user",
        tagline=cfg.get("tagline") or "",
        about=about,
        bio=bio if show_bio else "",
        location=user.get("location") or "",
        blog=user.get("blog") or "",
        twitter=user.get("twitter_username") or "",
        email=(cfg.get("email") or "").strip(),
        roles=roles,
        capabilities=capabilities,
        used_auto_skills=used_auto,
        principles=(cfg.get("principles") or "").strip(),
        open_to=(cfg.get("open_to") or "").strip(),
        languages=lang_rows,
        featured=featured,
        banner_path="./assets/argus-banner.svg",
        include_badges=bool(cfg.get("include_badges", True)),
        banner_carries_identity=bool(cfg.get("banner_carries_identity", True)),
        featured_card_width=int(cfg.get("featured_card_width") or 280),
    )


def needs_profile_update(existing: str | None, new_body: str) -> bool:
    if not existing:
        return True
    if MARKER not in existing:
        return True
    return existing.strip() != new_body.strip()
