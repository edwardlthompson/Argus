"""Canonical portfolio icon paths (config/profile_icons.yaml)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from argus.config_loader import load_yaml
from argus.paths import CONFIG_DIR

_FALLBACK_QUICK = (
    "branding/assets/app-icon-512.png",
    "branding/assets/logo-mark.png",
    "docs/brand/logo-official.png",
    "docs/brand/logo-neon-3d.png",
    "docs/assets/app-icon-512.png",
    "docs/assets/icon.png",
    "docs/assets/readme/app-icon.png",
    "docs/design/icon-reference-512.png",
    "branding/template/logo-mark.png",
    "apps/desktop/public/continuum-mark.png",
    "examples/desktop/src-tauri/icons/icon.png",
    "examples/desktop/src-tauri/icons/128x128.png",
    "examples/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png",
    "apps/mobile/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png",
    "fastlane/metadata/android/en-US/images/icon.png",
    "metadata/en-US/images/icon.png",
    "examples/android/metadata/en-US/images/icon.png",
    "apps/mobile/fastlane/metadata/android/en-US/images/icon.png",
    "branding/assets/app-icon-512.svg",
)


def load_icon_policy(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "profile_icons.yaml")
    if not path.exists():
        return {
            "canonical": list(_FALLBACK_QUICK[:5]),
            "fallbacks": list(_FALLBACK_QUICK[5:]),
            "stub_svg_max_bytes": 400,
            "stub_paths": ["branding/assets/app-icon-512.svg"],
        }
    data = load_yaml(path)
    return data if isinstance(data, dict) else {}


def stub_svg_max() -> int:
    return int(load_icon_policy().get("stub_svg_max_bytes") or 400)


def quick_paths() -> tuple[str, ...]:
    pol = load_icon_policy()
    paths = list(pol.get("canonical") or []) + list(pol.get("fallbacks") or [])
    for p in _FALLBACK_QUICK:
        if p not in paths:
            paths.append(p)
    return tuple(paths)


def canonical_paths() -> list[str]:
    return [str(p) for p in (load_icon_policy().get("canonical") or [])]


def stub_paths() -> list[str]:
    return [str(p) for p in (load_icon_policy().get("stub_paths") or [])]
