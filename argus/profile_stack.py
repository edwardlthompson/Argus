"""Aggregate live GitHub languages and map them to FOSS devicon slugs."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoPlan, RepoRecord

# GitHub language name -> devicons slug (jsDelivr). Unknowns are omitted from icons.
_DEVICON: dict[str, str] = {
    "Python": "python",
    "Kotlin": "kotlin",
    "Java": "java",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "HTML": "html5",
    "CSS": "css3",
    "Go": "go",
    "Rust": "rust",
    "C": "c",
    "C++": "cplusplus",
    "C#": "csharp",
    "PHP": "php",
    "Ruby": "ruby",
    "Swift": "swift",
    "Dart": "dart",
    "Shell": "bash",
    "PowerShell": "powershell",
    "Lua": "lua",
    "R": "r",
    "Scala": "scala",
    "Vue": "vuejs",
    "Dockerfile": "docker",
    "SCSS": "sass",
    "Svelte": "svelte",
    "Elixir": "elixir",
    "Haskell": "haskell",
    "Zig": "zig",
}


def _eligible(repo: RepoRecord) -> bool:
    return (
        not repo.private
        and not repo.archived
        and not repo.fork
        and repo.owner != repo.name
    )


def collect_language_bytes(client: GitHubClient, plans: list[RepoPlan]) -> dict[str, int]:
    """Sum language bytes across eligible repos; stash per-repo on raw."""
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


def ranked_languages(
    totals: dict[str, int], *, limit: int = 8
) -> list[dict[str, str]]:
    """Return [{name, slug, icon_url}] for languages with a known devicon."""
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    out: list[dict[str, str]] = []
    for name, _ in ranked:
        slug = _DEVICON.get(name)
        if not slug:
            continue
        out.append(
            {
                "name": name,
                "slug": slug,
                "icon_url": (
                    f"https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/"
                    f"{slug}/{slug}-original.svg"
                ),
            }
        )
        if len(out) >= limit:
            break
    return out


def language_names_from_plans(plans: list[RepoPlan]) -> list[str]:
    """Offline/tests: use bytes already on raw without API."""
    totals: dict[str, int] = {}
    for plan in plans:
        langs = (plan.repo.raw or {}).get("argus_languages") or {}
        if isinstance(langs, dict):
            for name, nbytes in langs.items():
                totals[str(name)] = totals.get(str(name), 0) + int(nbytes)
    return [row["name"] for row in ranked_languages(totals, limit=20)]
