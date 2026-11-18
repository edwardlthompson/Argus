"""Bump known Trivy-flagged Android/Gradle library pins on upgrade heads."""

from __future__ import annotations

from argus.github_client import GitHubClient
from argus.yolo_upgrade_heal import _exists, _get_raw, _put

_OLD = "32.0.1-android"
_NEW = "33.7.2"
_LOCK_PATHS = (
    "app/gradle.lockfile",
    "settings-gradle.lockfile",
    "gradle.lockfile",
    "examples/android/app/gradle.lockfile",
)
_ROOT_BUILD = ("build.gradle.kts", "examples/android/build.gradle.kts")
_GUAVA_STRATEGY = (
    '            if (requested.group == "com.google.guava" && requested.name == "guava") {\n'
    f'                useVersion("{_NEW}")\n'
    '                because("Align Guava for Trivy dependency scan (CVE-2026-102554)")\n'
    "            }\n"
)


def fix_trivy_gradle_guava(
    client: GitHubClient, owner: str, name: str, branch: str
) -> list[str]:
    """Bump Guava 32.0.1-android → 33.7.2 in lockfiles + resolutionStrategy."""
    actions: list[str] = []
    for path in _LOCK_PATHS:
        if not _exists(client, owner, name, path, branch):
            continue
        got = _get_raw(client, owner, name, path, branch)
        if got is None:
            continue
        text = got[0].decode("utf-8", errors="replace")
        if f"com.google.guava:guava:{_OLD}" not in text:
            continue
        new = text.replace(f"com.google.guava:guava:{_OLD}", f"com.google.guava:guava:{_NEW}")
        _put(
            client, owner, name, path, new.encode("utf-8"),
            f"chore(argus): lockfile Guava {_NEW} ({path})",
            branch, got[1],
        )
        actions.append(f"guava-lock:{path}")
    for path in _ROOT_BUILD:
        if not _exists(client, owner, name, path, branch):
            continue
        got = _get_raw(client, owner, name, path, branch)
        if got is None:
            continue
        text = got[0].decode("utf-8", errors="replace")
        if "CVE-2026-102554" in text or "resolutionStrategy.eachDependency" not in text:
            continue
        if _GUAVA_STRATEGY.strip() in text:
            continue
        # Insert before closing braces of eachDependency block when present.
        marker = "resolutionStrategy.eachDependency {"
        if marker not in text:
            continue
        # After last useVersion/because pair inside first eachDependency — append before its closing.
        idx = text.find(marker)
        close = text.find("\n            }\n", idx)
        if close < 0:
            continue
        new = text[:close] + "\n" + _GUAVA_STRATEGY.rstrip("\n") + text[close:]
        _put(
            client, owner, name, path, new.encode("utf-8"),
            f"chore(argus): force Guava {_NEW} for Trivy CVE ({path})",
            branch, got[1],
        )
        actions.append(f"guava-strategy:{path}")
    return actions
