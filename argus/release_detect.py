"""Pure release-freshness detection. Behaviour in config/releases.yaml."""

from __future__ import annotations

import re
from typing import Any

from argus.config_loader import load_releases

_GRADLE = re.compile(r'versionName(\s*[=:]?\s*)(["\'])([0-9][0-9.]*)\2')
_KINDS = {
    "gradle": (_GRADLE, None),
    "toml": (re.compile(r'(?m)^version\s*=\s*["\']([0-9][0-9.]*)["\']'), 'version = "{v}"'),
    "json": (re.compile(r'"version"\s*:\s*"([0-9][0-9.]*)"'), '"version": "{v}"'),
}


def cfg(data: dict[str, Any] | None = None) -> dict[str, Any]:
    return data if data is not None else load_releases()


def parse_semver(text: str | None) -> tuple[int, ...]:
    core = str(text or "").strip().lstrip("vV").split("-")[0]
    parts = [int(p) for p in core.split(".") if p.isdigit()][:3]
    return tuple(parts + [0] * (3 - len(parts))) if parts else ()


def next_version(tag: str | None, *, bump: str = "patch", source: str | None = None) -> str:
    src, tg = parse_semver(source), parse_semver(tag)
    if src and tg and src > tg:  # source already ahead of tag — do not bump again
        return f"{src[0]}.{src[1]}.{src[2]}"
    n = list(src or tg or (0, 1, 0))
    if bump == "minor":
        n[1], n[2] = n[1] + 1, 0
    else:
        n[2] += 1
    return f"{n[0]}.{n[1]}.{n[2]}"


def extract_version(text: str, kind: str) -> str | None:
    spec = _KINDS.get(kind)
    m = spec[0].search(text) if spec and text else None
    return (m.group(3) if kind == "gradle" else m.group(1)) if m else None


def bump_version_text(text: str, kind: str, new: str) -> str:
    spec = _KINDS.get(kind)
    if not spec or not text:
        return text
    pat, tmpl = spec
    if tmpl is None:
        return pat.sub(lambda m: f"versionName{m.group(1)}{m.group(2)}{new}{m.group(2)}", text, count=1)
    return pat.sub(tmpl.format(v=new), text, count=1)


def match_platforms(paths: list[str], config: dict[str, Any] | None = None) -> list[str]:
    names = {p.split("/")[-1] for p in paths}
    hits: list[str] = []
    for pid, rule in (cfg(config).get("platforms") or {}).items():
        if any(
            p.endswith(s) or p.endswith(s.lstrip("/")) or s.lstrip("/") in p
            for s in (str(x) for x in (rule.get("any_suffix") or [])) for p in paths
        ):
            hits.append(pid)
        elif any(n == str(x) for n in names for x in (rule.get("any_name") or [])):
            hits.append(pid)
        elif any(str(c) in p for c in (rule.get("any_contains") or []) for p in paths):
            hits.append(pid)
    return list(dict.fromkeys(hits))


def normalize_on(on: Any) -> dict[str, Any]:
    if isinstance(on, str):
        return {on: None}
    if isinstance(on, list):
        return {str(x): None for x in on}
    return {str(k): v for k, v in on.items()} if isinstance(on, dict) else {}


def hot_triggers(on: Any) -> list[str]:
    events = normalize_on(on)
    push = events.get("push")
    tags_only = isinstance(push, dict) and bool(push.get("tags")) and not push.get("branches")
    hot: list[str] = []
    if "pull_request" in events or "pull_request_target" in events:
        hot.append("pull_request")
    if "push" in events and not tags_only:
        hot.append("push")
    if "schedule" in events:
        hot.append("schedule")
    return hot


def use_authenticated_owner(owner: str | None, login: str | None, *, public_only: bool) -> bool:
    return bool(owner and login and str(owner).lower() == str(login).lower() and not public_only)

def skip_reason(repo: dict[str, Any], platforms: list[str], config: dict[str, Any] | None = None) -> str | None:
    c, skip = cfg(config), (cfg(config).get("skip") or {})
    full = str(repo.get("full_name") or "").lower()
    deny = {str(x).lower() for x in (skip.get("deny") or [])}
    allow = {str(x).lower() for x in (skip.get("allow") or [])}
    if full in deny:
        return "deny_list"
    if allow and full not in allow:
        return "not_allow_listed"
    status = str(repo.get("status") or "active")
    if status in (skip.get("statuses") or ["archived", "parked"]):
        return status
    if skip.get("forks", True) and repo.get("fork"):
        return "fork"
    if skip.get("profile_repos", True) and repo.get("owner") == repo.get("name"):
        return "profile_repo"
    docs = c.get("docs_only") or {}
    lang, topics = str(repo.get("language") or ""), {str(t).lower() for t in (repo.get("topics") or [])}
    doc = lang in (docs.get("languages") or []) or bool(topics & {str(t).lower() for t in (docs.get("topics") or [])})
    if skip.get("docs_only", True) and doc and not platforms:
        return "docs_only"
    return None if platforms else "releases_not_applicable"


def evaluate(facts: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    c, platforms, rules = cfg(config), list(facts.get("platforms") or []), (cfg(config).get("platforms") or {})
    skip, stale_n = skip_reason(facts, platforms, c), int(c.get("stale_days") or 90)
    days, ahead = facts.get("days_since_release"), int(facts.get("ahead_by") or 0)
    stale = bool(facts.get("has_release") and days is not None and int(days) >= stale_n and ahead > 0)
    missing_release = not bool(facts.get("has_release"))
    assets = [str(a).lower() for a in (facts.get("asset_names") or [])]
    missing_art = [
        pid for pid in platforms
        if facts.get("has_release") and (suf := [str(s).lower() for s in (rules.get(pid) or {}).get("artifacts") or []])
        and not any(a.endswith(s) for a in assets for s in suf)
    ]
    src, tag = parse_semver(facts.get("source_version")), parse_semver(facts.get("latest_tag"))
    mismatch, no_wf = bool(src and tag and src != tag), not bool(facts.get("has_tag_release_workflow"))
    missing = [k for k, v in (
        ("missing release", missing_release), (f"stale (>{stale_n}d with commits since)", stale),
        ("missing artifacts: " + ", ".join(missing_art), bool(missing_art)),
        ("source version != last tag", mismatch), ("no tag-triggered release workflow", no_wf),
    ) if v]
    has_tmpl = any((rules.get(p) or {}).get("template") for p in platforms)
    irreg = facts.get("irregular_reason") or ("no_template" if platforms and not has_tmpl else None)
    eligible, needs = skip is None, skip is None and bool(missing)
    nxt = next_version(facts.get("latest_tag"), bump=str(c.get("bump") or "patch"), source=facts.get("source_version"))
    return {
        "skip": skip, "eligible": eligible, "missing_release": missing_release and eligible,
        "stale": stale and eligible, "missing_artifacts": missing_art if eligible else [],
        "version_mismatch": mismatch and eligible, "no_release_workflow": no_wf and eligible,
        "needs_prep": needs, "irregular": bool(irreg) and needs, "irregular_reason": irreg if needs else None,
        "missing": missing if eligible else [], "next_version": nxt, "next_tag": f"v{nxt}", "stale_days": stale_n,
    }
