#!/usr/bin/env python3
"""Open one PR per child: parent v1.13.0 canon rules + .template-version.

Does not overwrite sacred paths (AGENTS.md, docs/spec.md, docs/plan.md, branding/assets).
Does not force-push. Skips parent / profile / runner by default.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

PARENT = "edwardlthompson/agent-project-bootstrap"
PARENT_REF = "v1.13.0"
TARGET_VER = "1.13.0"
BRANCH = "chore/argus-upgrade-1.13.0"

SKIP = frozenset({
    "edwardlthompson/agent-project-bootstrap",
    "edwardlthompson/edwardlthompson",
    "edwardlthompson/argus-runner",
})

# Product Argus: Python package owns argus/ — use cursor rules + docs + contract only.
ARGUS_PRODUCT = "edwardlthompson/Argus"

CANON = [
    ".cursor/rules/brand-icon.mdc",
    ".cursor/rules/ux-law.mdc",
    "argus/rules/brand-icon.yaml",
    "argus/rules/layout.yaml",
    "argus/rules/orphans.yaml",
    "argus/rules/ux-law.yaml",
    "argus/ux/rules/ux-compose-hardcoded-color.yaml",
    "argus/ux/rules/ux-raw-hex.yaml",
    "argus.contract.json",
    "argus.remote.json",
    "rules.manifest.json",
    "config/orphan-exceptions.yaml",
    "ux-baseline.json",
    "docs/BRAND_ICON.md",
    "docs/UX_LAW.md",
    "docs/LAYOUT.md",
    "docs/YOLO.md",
    "docs/FLEET.md",
    "docs/ARGUS_REMOTE.md",
    "docs/RELEASE_TOKENS.md",
    ".github/workflows/argus-rules-manifest.yml",
    ".github/workflows/argus-remote-stub.yml",
]

CANON_ARGUS_PRODUCT = [
    ".cursor/rules/brand-icon.mdc",
    ".cursor/rules/ux-law.mdc",
    "argus/ux/rules/ux-compose-hardcoded-color.yaml",
    "argus/ux/rules/ux-raw-hex.yaml",
    "argus.remote.json",
    "docs/BRAND_ICON.md",
    "docs/UX_LAW.md",
    "docs/LAYOUT.md",
    "docs/FLEET.md",
    "docs/ARGUS_REMOTE.md",
    "docs/RELEASE_TOKENS.md",
]


def api(method: str, path: str, token: str, body: dict | None = None) -> dict | list | None:
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "argus-child-upgrade",
        },
    )
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=120) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        err = exc.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path}: {exc.code} {err[:400]}") from exc


def get_file(token: str, repo: str, path: str, ref: str) -> bytes | None:
    try:
        data = api("GET", f"/repos/{repo}/contents/{path}?ref={ref}", token)
    except RuntimeError as exc:
        if "404" in str(exc):
            return None
        raise
    if not isinstance(data, dict) or not data.get("content"):
        return None
    return base64.b64decode(data["content"])


def put_file(
    token: str,
    repo: str,
    path: str,
    content: bytes,
    message: str,
    branch: str,
) -> None:
    owner, name = repo.split("/", 1)
    b64 = base64.b64encode(content).decode("ascii")
    payload: dict = {"message": message, "content": b64, "branch": branch}
    try:
        existing = api(
            "GET",
            f"/repos/{owner}/{name}/contents/{path}?ref={branch}",
            token,
        )
        if isinstance(existing, dict) and existing.get("sha"):
            payload["sha"] = existing["sha"]
    except RuntimeError as exc:
        if "404" not in str(exc):
            raise
    api("PUT", f"/repos/{owner}/{name}/contents/{path}", token, payload)


def ensure_branch(token: str, repo: str) -> str:
    owner, name = repo.split("/", 1)
    meta = api("GET", f"/repos/{owner}/{name}", token)
    assert isinstance(meta, dict)
    default = str(meta.get("default_branch") or "main")
    ref = api("GET", f"/repos/{owner}/{name}/git/ref/heads/{default}", token)
    assert isinstance(ref, dict)
    sha = ref["object"]["sha"]
    try:
        api(
            "POST",
            f"/repos/{owner}/{name}/git/refs",
            token,
            {"ref": f"refs/heads/{BRANCH}", "sha": sha},
        )
    except RuntimeError as exc:
        if "422" not in str(exc):
            raise
    return default


def open_pr(token: str, repo: str, default: str, body: str) -> str:
    owner, name = repo.split("/", 1)
    try:
        pr = api(
            "POST",
            f"/repos/{owner}/{name}/pulls",
            token,
            {
                "title": f"chore(argus): upgrade parent rules to {TARGET_VER}",
                "head": BRANCH,
                "base": default,
                "body": body,
            },
        )
        assert isinstance(pr, dict)
        return str(pr.get("html_url") or "")
    except RuntimeError as exc:
        if "422" not in str(exc):
            raise
        existing = api(
            "GET",
            f"/repos/{owner}/{name}/pulls?state=open&head={owner}:{BRANCH}&per_page=5",
            token,
        )
        if isinstance(existing, list) and existing:
            return str(existing[0].get("html_url") or "")
        return f"existing:{repo}"


def upgrade_repo(token: str, repo: str, *, dry_run: bool = False) -> dict:
    if repo in SKIP:
        return {"repo": repo, "status": "skipped_excluded"}
    paths = CANON_ARGUS_PRODUCT if repo == ARGUS_PRODUCT else CANON
    files: list[tuple[str, bytes]] = []
    for path in paths:
        blob = get_file(token, PARENT, path, PARENT_REF)
        if blob is None:
            continue
        files.append((path, blob))
    files.append((".template-version", f"{TARGET_VER}\n".encode()))
    if dry_run:
        return {"repo": repo, "status": "dry_run", "files": [p for p, _ in files]}
    default = ensure_branch(token, repo)
    for path, blob in files:
        put_file(
            token,
            repo,
            path,
            blob,
            f"chore(argus): sync {path} from {PARENT}@{PARENT_REF}",
            BRANCH,
        )
    body = (
        f"## Parent upgrade `{PARENT_REF}`\n\n"
        f"Argus automatic child upgrade (canon rules + markers).\n\n"
        f"- Parent: `{PARENT}` @ `{PARENT_REF}`\n"
        f"- `.template-version` → `{TARGET_VER}`\n"
        f"- Files: {len(files)} (no sacred overwrites; no branding assets)\n\n"
        f"### Gate\n`python scripts/agent-run.py verify` or project verify if present.\n"
    )
    url = open_pr(token, repo, default, body)
    return {"repo": repo, "status": "opened", "pr": url, "files": len(files)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="+", help="owner/name …")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ARGUS_GITHUB_TOKEN")
    if not token:
        # fall back to gh
        token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    out = []
    for repo in args.repos:
        try:
            out.append(upgrade_repo(token, repo, dry_run=args.dry_run))
        except Exception as exc:  # noqa: BLE001
            out.append({"repo": repo, "status": "error", "error": str(exc)[:500]})
            print(json.dumps(out[-1]), flush=True)
            return 1
        print(json.dumps(out[-1]), flush=True)
    Path("dist").mkdir(exist_ok=True)
    Path("dist/upgrade-wave.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
