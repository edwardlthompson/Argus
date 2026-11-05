"""Derive portfolio skill cards from live languages/topics (no LLM)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from argus.config_loader import load_yaml
from argus.models import RepoPlan
from argus.paths import CONFIG_DIR
from argus.profile_featured import _eligible

# Short / meme GitHub bios that should not appear under a portfolio About.
_BIO_SKIP = frozenset(
    {
        "just vibes",
        "just vibes.",
        "vibes",
        "n/a",
        "na",
        "none",
        "todo",
        "tbd",
        "...",
        ".",
        "-",
    }
)


def load_profile_skills(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "profile_skills.yaml")
    if not path.exists():
        return {"roles": [], "capabilities": []}
    data = load_yaml(path)
    return data if isinstance(data, dict) else {"roles": [], "capabilities": []}


def _portfolio_signals(plans: list[RepoPlan]) -> set[str]:
    signals: set[str] = set()
    for plan in plans:
        if not _eligible(plan.repo):
            continue
        for t in plan.repo.topics:
            signals.add(str(t).strip().lower())
        langs = (plan.repo.raw or {}).get("argus_languages") or {}
        if isinstance(langs, dict):
            for name in langs:
                signals.add(str(name).strip().lower())
    return signals


def _match_cards(
    cards: list[dict[str, Any]], signals: set[str], *, limit: int
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for card in cards:
        match = {str(m).lower() for m in (card.get("match") or [])}
        if not match or match.isdisjoint(signals):
            continue
        title = str(card.get("title") or "").strip()
        blurb = str(card.get("blurb") or "").strip()
        if not title:
            continue
        out.append({"title": title, "blurb": blurb})
        if len(out) >= limit:
            break
    return out


def resolve_roles_and_capabilities(
    plans: list[RepoPlan],
    cfg: dict[str, Any],
    *,
    skills: dict[str, Any] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], bool]:
    """Return (roles, capabilities, used_auto). YAML overrides win when non-empty."""
    yaml_roles = [r for r in (cfg.get("roles") or []) if isinstance(r, dict) and r.get("title")]
    yaml_caps = [
        c for c in (cfg.get("capabilities") or []) if isinstance(c, dict) and c.get("title")
    ]
    if yaml_roles or yaml_caps:
        roles = [{"title": str(r["title"]), "blurb": str(r.get("blurb") or "")} for r in yaml_roles]
        caps = [{"title": str(c["title"]), "blurb": str(c.get("blurb") or "")} for c in yaml_caps]
        return roles, caps, False

    skill_cfg = skills if skills is not None else load_profile_skills()
    signals = _portfolio_signals(plans)
    roles = _match_cards(list(skill_cfg.get("roles") or []), signals, limit=4)
    caps = _match_cards(list(skill_cfg.get("capabilities") or []), signals, limit=6)
    return roles, caps, True


def auto_about(languages: list[str], featured_names: list[str]) -> str:
    """Short portfolio blurb from live evidence only."""
    lang_bit = ", ".join(languages[:4]) if languages else "practical tools"
    feat_bit = ", ".join(featured_names[:3]) if featured_names else "public projects"
    return (
        f"I build maintainable software across {lang_bit}. "
        f"Featured work includes {feat_bit}. "
        "Argus keeps this Overview aligned with live repositories — "
        "a portfolio of skills and clean, secure apps."
    )


def bio_is_distinct(about: str, bio: str) -> bool:
    """Show GitHub bio only when it adds signal (not throwaway / duplicate)."""
    b = bio.strip()
    if not b:
        return False
    if b.lower() in _BIO_SKIP:
        return False
    if len(b) < 12:
        return False
    a = about.strip().lower()
    bl = b.lower()
    if not a:
        return True
    return bl not in a and a not in bl
