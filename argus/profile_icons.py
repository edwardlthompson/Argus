"""Resolve app/brand icons from target repos (raster paths + git tree scan)."""

from __future__ import annotations

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord
from argus.profile_icon_policy import quick_paths

_SKIP = ("/third_party/", "/concepts/", "/node_modules/", "/.git/", "/.cursor/", "fossify-")
_REJECT_BASE = (
    "social-preview",
    "splash",
    "readme-hero",
    "favicon",
    "wordmark",
    "lockup",
    "github-social",
)


def _score_icon_path(path: str, size: int | None = None) -> int | None:
    del size  # reserved for future size heuristics
    low = path.replace("\\", "/").lower()
    if any(s in low for s in _SKIP):
        return None
    if not low.endswith((".png", ".webp", ".jpg", ".jpeg")):
        return None
    base = low.rsplit("/", 1)[-1]
    if any(x in base for x in _REJECT_BASE) or "foreground" in base or "round" in base:
        return None
    score = 30 if low.endswith(".png") else 5
    if "docs/brand/" in low:
        score += 120
    elif base in {"continuum-mark.png", "logo-official.png", "logo-neon-3d.png"}:
        score += 115
    elif "branding/assets/" in low and base.endswith(".png"):
        score += 110
    elif "branding/template/" in low and base == "logo-mark.png":
        score += 100
    elif "src-tauri/icons/" in low and base in {"icon.png", "128x128.png", "app-icon.png"}:
        score += 95
    elif "mipmap-xxxhdpi/" in low and base == "ic_launcher.png":
        score += 88
    elif "docs/assets/" in low or "docs/design/" in low:
        score += 90
    elif "/public/" in low and "continuum" in base:
        score += 85
    elif "fastlane/" in low or "/metadata/" in low:
        score += 55
    elif "branding/assets/" in low:
        score += 50
    if base in {
        "logo-official.png",
        "logo-neon-3d.png",
        "continuum-mark.png",
        "logo-mark.png",
        "app-icon-512.png",
    }:
        score += 100
    elif base.startswith("app-icon-512.") and base.endswith(".png"):
        score += 95
    elif base in {"icon.png", "app-icon.png", "logo.png", "brand.png"}:
        score += 80
    elif base == "ic_launcher.png":
        score += 60
    elif "ic_launcher" in base:
        score += 20
    else:
        return None
    return score


def pick_icon_path(
    paths: list[str], *, sizes: dict[str, int] | None = None
) -> str | None:
    sizes = sizes or {}
    best: tuple[int, str] | None = None
    for path in paths:
        score = _score_icon_path(path, sizes.get(path))
        if score is None:
            continue
        if best is None or score > best[0]:
            best = (score, path)
    return best[1] if best else None


def resolve_icon(client: GitHubClient, repo: RepoRecord) -> str | None:
    """Prefer product brand PNGs; Overview never uses SVG (generate PNG instead)."""
    for path in quick_paths():
        if path.lower().endswith(".svg"):
            continue
        try:
            data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
        except GitHubError:
            continue
        if not isinstance(data, dict) or not data.get("download_url"):
            continue
        if int(data.get("size") or 0) <= 0:
            continue
        return str(data["download_url"])
    try:
        meta = client.get_repo(repo.owner, repo.name)
        branch = str(meta.get("default_branch") or repo.default_branch or "main")
        tree = client.get(
            f"/repos/{repo.owner}/{repo.name}/git/trees/{branch}",
            params={"recursive": "1"},
        )
    except GitHubError:
        return None
    blobs: list[str] = []
    sizes: dict[str, int] = {}
    for node in tree.get("tree") or []:
        if node.get("type") != "blob" or not node.get("path"):
            continue
        path = str(node["path"])
        blobs.append(path)
        if "size" in node:
            sizes[path] = int(node["size"] or 0)
    ranked = sorted(
        ((s, p) for p in blobs if (s := _score_icon_path(p, sizes.get(p))) is not None),
        key=lambda t: -t[0],
    )
    for _, chosen in ranked[:12]:
        try:
            data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/{chosen}")
        except GitHubError:
            continue
        if isinstance(data, dict) and data.get("download_url"):
            return str(data["download_url"])
    return None
