"""Aggregate live GitHub languages and map them to FOSS devicon stack groups."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from argus.config_loader import load_yaml
from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoPlan, RepoRecord
from argus.paths import CONFIG_DIR

# Signal (language/topic, lower) -> devicons slug.
_DEVICON = {
    "python": "python",
    "kotlin": "kotlin",
    "java": "java",
    "javascript": "javascript",
    "typescript": "typescript",
    "html": "html5",
    "html5": "html5",
    "css": "css3",
    "css3": "css3",
    "go": "go",
    "rust": "rust",
    "c": "c",
    "c++": "cplusplus",
    "c#": "csharp",
    "csharp": "csharp",
    "php": "php",
    "swift": "swift",
    "dart": "dart",
    "shell": "bash",
    "bash": "bash",
    "powershell": "powershell",
    "docker": "docker",
    "dockerfile": "docker",
    "android": "android",
    "git": "git",
    "sqlite": "sqlite",
}


def _eligible(repo: RepoRecord) -> bool:
    return (
        not repo.private
        and not repo.archived
        and not repo.fork
        and repo.owner != repo.name
    )


def _icon_row(signal: str, display: str | None = None) -> dict[str, str] | None:
    slug = _DEVICON.get(signal.lower())
    if not slug:
        return None
    return {
        "name": display or signal,
        "slug": slug,
        "icon_url": (
            f"https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/"
            f"{slug}/{slug}-original.svg"
        ),
    }


def collect_language_bytes(client: GitHubClient, plans: list[RepoPlan]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for plan in plans:
        repo = plan.repo
        if not _eligible(repo):
            continue
        raw: dict[str, Any] = dict(repo.raw or {})
        try:
            langs = client.get(f"/repos/{repo.owner}/{repo.name}/languages")
        except GitHubError:
            langs = {}
        if not isinstance(langs, dict):
            langs = {}
        raw["argus_languages"] = {str(k): int(v) for k, v in langs.items()}
        repo.raw = raw
        for name, nbytes in raw["argus_languages"].items():
            totals[name] = totals.get(name, 0) + int(nbytes)
    return totals


def ranked_languages(totals: dict[str, int], *, limit: int = 8) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for name, _ in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])):
        row = _icon_row(name, name)
        if row:
            out.append(row)
        if len(out) >= limit:
            break
    return out


def load_stack_groups(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or (CONFIG_DIR / "profile_stack.yaml")
    if not path.exists():
        return []
    data = load_yaml(path)
    if not isinstance(data, dict):
        return []
    return [g for g in (data.get("groups") or []) if isinstance(g, dict) and g.get("title")]


def portfolio_signals(plans: list[RepoPlan], totals: dict[str, int]) -> set[str]:
    signals = {str(n).lower() for n in totals}
    for plan in plans:
        if _eligible(plan.repo):
            signals.update(str(t).strip().lower() for t in plan.repo.topics)
    return signals


def grouped_stack(
    plans: list[RepoPlan],
    totals: dict[str, int],
    *,
    groups: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    signals = portfolio_signals(plans, totals)
    canon = {n.lower(): n for n in totals}
    out: list[dict[str, Any]] = []
    for group in groups if groups is not None else load_stack_groups():
        limit = int(group.get("limit") or 8)
        icons: list[dict[str, str]] = []
        seen: set[str] = set()
        for m in (str(x).lower() for x in (group.get("match") or [])):
            if m not in signals or m in seen:
                continue
            row = _icon_row(m, canon.get(m) or m.replace("-", " ").title())
            if not row:
                continue
            icons.append(row)
            seen.add(m)
            if len(icons) >= limit:
                break
        if icons:
            out.append({"title": str(group["title"]), "icons": icons})
    return out
