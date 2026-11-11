"""Deterministic npm CVE overrides for YOLO Trivy FS / dependency failures."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.yolo_upgrade_heal import _exists, _get_raw, _put

# Fixed floors for recurring HIGH/CRITICAL Trivy library hits (upgrade-wave catalog).
NPM_OVERRIDES: dict[str, str] = {
    "@xmldom/xmldom": "0.9.12",
    "brace-expansion": "5.0.11",
}
CAPACITOR_PINS: dict[str, str] = {
    "@capacitor/android": "8.5.1",
    "@capacitor/cli": "8.5.1",
    "@capacitor/core": "8.5.1",
}

_PKG_CANDIDATES = (
    "package.json",
    "examples/web/package.json",
    "examples/node/package.json",
    "signaling-server/package.json",
)


def _lock_path(pkg_path: str) -> str:
    return pkg_path.rsplit("/", 1)[0] + "/package-lock.json" if "/" in pkg_path else "package-lock.json"


def _apply_pkg_json(data: dict[str, Any]) -> bool:
    changed = False
    overrides = dict(data.get("overrides") or {})
    for k, v in NPM_OVERRIDES.items():
        if overrides.get(k) != v:
            overrides[k] = v
            changed = True
    if overrides != (data.get("overrides") or {}):
        data["overrides"] = overrides
        changed = True
    for bag_name in ("dependencies", "devDependencies"):
        bag = data.get(bag_name)
        if not isinstance(bag, dict):
            continue
        for k, pin in CAPACITOR_PINS.items():
            cur = bag.get(k)
            if isinstance(cur, str) and re.search(r"8\.4\.[0-2]|^8\.4\.2$", cur.lstrip("^~")):
                bag[k] = pin
                changed = True
    return changed


def _npm_bin() -> str | None:
    return shutil.which("npm.cmd") or shutil.which("npm")


def _regen_lock(pkg_dir: Path) -> bool:
    npm = _npm_bin()
    if not npm:
        return False
    try:
        subprocess.run(
            [npm, "install", "--package-lock-only", "--ignore-scripts"],
            cwd=str(pkg_dir),
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def fix_trivy_npm_overrides(
    client: GitHubClient, owner: str, name: str, branch: str
) -> list[str]:
    """Add known npm overrides + regen lockfiles on upgrade heads with package.json."""
    actions: list[str] = []
    for pkg_path in _PKG_CANDIDATES:
        if not _exists(client, owner, name, pkg_path, branch):
            continue
        got = _get_raw(client, owner, name, pkg_path, branch)
        if got is None:
            continue
        raw, sha = got
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if not _apply_pkg_json(data):
            # Still try lock regen if overrides already present but lock stale.
            pass
        new_pkg = (json.dumps(data, indent=2) + "\n").encode("utf-8")
        pkg_changed = new_pkg != raw
        lock_path = _lock_path(pkg_path)
        lock_got = _get_raw(client, owner, name, lock_path, branch)
        if not pkg_changed and lock_got is None:
            continue
        with tempfile.TemporaryDirectory(prefix="argus-trivy-") as tmp:
            tdir = Path(tmp)
            rel_dir = Path(pkg_path).parent
            work = tdir / rel_dir if str(rel_dir) != "." else tdir
            work.mkdir(parents=True, exist_ok=True)
            (work / "package.json").write_bytes(new_pkg)
            if lock_got is not None:
                (work / "package-lock.json").write_bytes(lock_got[0])
            lock_ok = _regen_lock(work)
            if pkg_changed:
                _put(
                    client, owner, name, pkg_path, new_pkg,
                    f"chore(argus): npm overrides for Trivy CVEs ({pkg_path})",
                    branch, sha,
                )
                actions.append(f"npm-overrides:{pkg_path}")
            if lock_ok and (work / "package-lock.json").is_file():
                new_lock = (work / "package-lock.json").read_bytes()
                lock_sha = lock_got[1] if lock_got else None
                if lock_got is None or new_lock != lock_got[0]:
                    try:
                        _put(
                            client, owner, name, lock_path, new_lock,
                            f"chore(argus): lockfile for Trivy npm overrides ({lock_path})",
                            branch, lock_sha,
                        )
                        actions.append(f"npm-lock:{lock_path}")
                    except GitHubError:
                        pass
    return actions
