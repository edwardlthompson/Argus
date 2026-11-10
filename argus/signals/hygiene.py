"""Hygiene: license SPDX, community files, stale branches, CODEOWNERS, brand icon state."""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord

_STALE_DAYS = 90
_PLACEHOLDER_BYTES = 400
_REJECT_BASE = frozenset({
    "social-preview",
    "splash",
    "readme-hero",
    "favicon",
    "wordmark",
    "lockup",
    "foreground",
    "round",
    "og-image",
    "twitter-card",
})


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    spdx: str | None = None
    license_ok = False
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/license")
        lic = data.get("license") or {}
        spdx = lic.get("spdx_id")
        license_ok = bool(lic)
    except GitHubError:
        pass

    brand = _brand_icon(client, repo)
    return {
        "security_md": _exists(client, repo, "SECURITY.md"),
        "contributing_md": _exists(client, repo, "CONTRIBUTING.md"),
        "code_of_conduct_md": _exists(client, repo, "CODE_OF_CONDUCT.md"),
        "codeowners": _exists(client, repo, "CODEOWNERS")
        or _exists(client, repo, ".github/CODEOWNERS")
        or _exists(client, repo, "docs/CODEOWNERS"),
        "gitattributes": _exists(client, repo, ".gitattributes"),
        "gitignore": _exists(client, repo, ".gitignore"),
        "license_file": license_ok
        or _exists(client, repo, "LICENSE")
        or _exists(client, repo, "LICENSE.md"),
        "agent_files_at_root": _exists(client, repo, "AGENT_MEMORY.md"),
        "license_spdx": spdx,
        "stale_branch_count": _stale_branches(client, repo),
        "branch_protection": _branch_protection(client, repo),
        "actions_runs_30d": _actions_runs(client, repo),
        **brand,
    }


def _exists(client: GitHubClient, repo: RepoRecord, path: str) -> bool:
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        return True
    except GitHubError:
        return False


def _basename_stem(path: str) -> str:
    return Path(path).stem.lower().replace("_", "-")


def _is_rejected_basename(path: str) -> bool:
    stem = _basename_stem(path)
    return any(token in stem for token in _REJECT_BASE)


def _sha256_content(data: dict[str, Any]) -> str | None:
    raw = data.get("content")
    if not isinstance(raw, str):
        return None
    try:
        blob = base64.b64decode(raw)
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(blob).hexdigest()


def _parent_icon_hashes() -> set[str]:
    """Optional parent manifest of inherited icon digests (config/parent_icons.sha256)."""
    from argus.paths import ROOT

    path = ROOT / "config" / "parent_icons.sha256"
    if not path.is_file():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        bit = line.strip().split()[0] if line.strip() and not line.strip().startswith("#") else ""
        if len(bit) == 64:
            out.add(bit.lower())
    return out


def classify_brand_icon(
    *,
    path: str | None,
    size: int,
    sha256: str | None,
    parent_hashes: set[str],
    stub_svg_max: int,
) -> str:
    """Pure classifier for tests: owned | inherited | missing | placeholder."""
    if not path:
        return "missing"
    if _is_rejected_basename(path):
        return "placeholder"
    if size < _PLACEHOLDER_BYTES:
        return "placeholder"
    if path.lower().endswith(".svg") and size <= stub_svg_max:
        return "placeholder"
    if sha256 and sha256.lower() in parent_hashes:
        return "inherited"
    return "owned"


def _brand_icon(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    """Canonical Overview icons — owned only passes. See docs/PROFILE_ICONS.md."""
    from argus.profile_icon_policy import canonical_paths, stub_paths, stub_svg_max

    max_stub = stub_svg_max()
    parent_hashes = _parent_icon_hashes()
    seen_placeholder = False
    for path in canonical_paths():
        if _is_rejected_basename(path):
            continue
        try:
            data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        except GitHubError:
            continue
        if not isinstance(data, dict):
            continue
        size = int(data.get("size") or 0)
        digest = _sha256_content(data)
        state = classify_brand_icon(
            path=path,
            size=size,
            sha256=digest,
            parent_hashes=parent_hashes,
            stub_svg_max=max_stub,
        )
        if state == "placeholder":
            seen_placeholder = True
            continue
        return {
            "brand_icon_ok": state == "owned",
            "brand_icon_state": state,
            "brand_icon_path": path,
            "brand_icon_stub_svg": state == "placeholder",
            "brand_icon_sha256": digest,
        }
    for path in stub_paths():
        try:
            data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        except GitHubError:
            continue
        if isinstance(data, dict) and int(data.get("size") or 0) <= max_stub:
            seen_placeholder = True
            break
    state = "placeholder" if seen_placeholder else "missing"
    return {
        "brand_icon_ok": False,
        "brand_icon_state": state,
        "brand_icon_path": None,
        "brand_icon_stub_svg": seen_placeholder,
        "brand_icon_sha256": None,
    }


def _stale_branches(client: GitHubClient, repo: RepoRecord) -> int:
    try:
        branches = client.get(
            f"/repos/{repo.owner}/{repo.name}/branches",
            params={"per_page": 30},
        )
    except GitHubError:
        return 0
    now = datetime.now(UTC)
    stale = 0
    default = repo.default_branch
    for br in branches or []:
        name = br.get("name") or ""
        if name == default:
            continue
        try:
            commit = client.get(
                f"/repos/{repo.owner}/{repo.name}/commits/{br.get('commit', {}).get('sha', name)}"
            )
            date_s = ((commit.get("commit") or {}).get("committer") or {}).get("date")
            if not date_s:
                continue
            when = datetime.fromisoformat(date_s.replace("Z", "+00:00"))
            if (now - when).days >= _STALE_DAYS:
                stale += 1
        except (GitHubError, TypeError, ValueError):
            continue
    return stale


def _branch_protection(client: GitHubClient, repo: RepoRecord) -> bool | None:
    try:
        client.get(f"/repos/{repo.owner}/{repo.name}/branches/{repo.default_branch}/protection")
        return True
    except GitHubError as exc:
        if "404" in str(exc):
            return False
        return None


def _actions_runs(client: GitHubClient, repo: RepoRecord) -> int | None:
    try:
        data = client.get(
            f"/repos/{repo.owner}/{repo.name}/actions/runs",
            params={"per_page": 30},
        )
        return int(data.get("total_count") or len(data.get("workflow_runs") or []))
    except GitHubError:
        return None
