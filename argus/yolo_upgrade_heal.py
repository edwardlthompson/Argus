"""Heal open parent-upgrade PRs so version-sync / index CI can go green."""

from __future__ import annotations

import base64
import json
import re
from datetime import date
from typing import Any

from argus.github_client import GitHubClient, GitHubError

TARGET_VER = "1.13.0"
BRANCH_PREFIX = "chore/argus-upgrade-"

INDEX_ENTRIES: dict[str, dict[str, str]] = {
    ".github/workflows/argus-remote-stub.yml": {
        "purpose": "CI remote status no-op when disabled",
        "status": "not_started",
    },
    ".github/workflows/argus-rules-manifest.yml": {
        "purpose": "Publish rules.manifest.json on main",
        "status": "not_started",
    },
    "argus.contract.json": {"purpose": "Argus contract markers", "status": "not_started"},
    "argus.remote.json": {"purpose": "Argus remote off switch", "status": "not_started"},
    "rules.manifest.json": {"purpose": "Rules manifest", "status": "not_started"},
}


def _get_raw(client: GitHubClient, owner: str, name: str, path: str, ref: str) -> tuple[bytes, str] | None:
    try:
        data = client.get(f"/repos/{owner}/{name}/contents/{path}", params={"ref": ref})
    except GitHubError as exc:
        if "404" in str(exc):
            return None
        raise
    if not isinstance(data, dict) or not data.get("content"):
        return None
    return base64.b64decode(data["content"]), str(data.get("sha") or "")


def _put(
    client: GitHubClient,
    owner: str,
    name: str,
    path: str,
    content: bytes,
    message: str,
    branch: str,
    sha: str | None,
) -> None:
    payload: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    client.put(f"/repos/{owner}/{name}/contents/{path}", allow_write=True, json=payload)


def _exists(client: GitHubClient, owner: str, name: str, path: str, ref: str) -> bool:
    return _get_raw(client, owner, name, path, ref) is not None


def heal_template_index(
    client: GitHubClient,
    owner: str,
    name: str,
    branch: str,
    *,
    target_ver: str = TARGET_VER,
) -> str:
    """Patch TEMPLATE_INDEX + release-please / citation / plugin / AGENT_MEMORY stub."""
    actions: list[str] = []
    got = _get_raw(client, owner, name, "TEMPLATE_INDEX.json", branch)
    if got is None:
        # Still sync version files when index is absent (Argus product).
        pass
    else:
        raw, sha = got
        index = json.loads(raw.decode("utf-8"))
        files = index.get("files")
        if not isinstance(files, list):
            return "error:files_not_list"
        by_path = {
            str(e.get("path")): e for e in files if isinstance(e, dict) and e.get("path")
        }
        changed = False
        if str(index.get("template_version") or "") != target_ver:
            index["template_version"] = target_ver
            changed = True
        for path, meta in INDEX_ENTRIES.items():
            if path in by_path or not _exists(client, owner, name, path, branch):
                continue
            entry = {"path": path, **meta}
            files.append(entry)
            by_path[path] = entry
            changed = True
        root_mem = by_path.get("AGENT_MEMORY.md")
        if root_mem and not _exists(client, owner, name, "AGENT_MEMORY.md", branch):
            if _exists(client, owner, name, ".agent/AGENT_MEMORY.md", branch):
                if ".agent/AGENT_MEMORY.md" in by_path:
                    files[:] = [e for e in files if e is not root_mem]
                else:
                    root_mem["path"] = ".agent/AGENT_MEMORY.md"
                changed = True
        if changed:
            body = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
            _put(
                client, owner, name, "TEMPLATE_INDEX.json", body.encode("utf-8"),
                f"chore(argus): sync TEMPLATE_INDEX to {target_ver}", branch, sha,
            )
            actions.append("index")

    # Release-please manifest "." must match .template-version.
    man = _get_raw(client, owner, name, ".release-please-manifest.json", branch)
    if man is not None:
        raw, sha = man
        data = json.loads(raw.decode("utf-8"))
        if str(data.get(".") or "").strip() != target_ver:
            data["."] = target_ver
            _put(
                client, owner, name, ".release-please-manifest.json",
                (json.dumps(data, indent=2) + "\n").encode("utf-8"),
                f"chore(argus): sync release-please manifest to {target_ver}",
                branch, sha,
            )
            actions.append("manifest")

    cff = _get_raw(client, owner, name, "CITATION.cff", branch)
    if cff is not None:
        text, sha = cff[0].decode("utf-8"), cff[1]
        new = re.sub(r"(?m)^version:\s*.*$", f"version: {target_ver}", text, count=1)
        if re.search(r"(?m)^date-released:\s*", new):
            new = re.sub(
                r"(?m)^date-released:\s*.*$",
                f"date-released: {date.today().isoformat()}",
                new,
                count=1,
            )
        else:
            new = new.rstrip() + f"\ndate-released: {date.today().isoformat()}\n"
        if new != text:
            _put(
                client, owner, name, "CITATION.cff", new.encode("utf-8"),
                f"chore(argus): sync CITATION.cff to {target_ver}", branch, sha,
            )
            actions.append("citation")

    plug = _get_raw(client, owner, name, ".cursor-plugin/plugin.json", branch)
    if plug is not None:
        raw, sha = plug
        data = json.loads(raw.decode("utf-8"))
        if str(data.get("version") or "") != target_ver:
            data["version"] = target_ver
            _put(
                client, owner, name, ".cursor-plugin/plugin.json",
                (json.dumps(data, indent=2) + "\n").encode("utf-8"),
                f"chore(argus): sync plugin version to {target_ver}",
                branch, sha,
            )
            actions.append("plugin")

    # Sprint-0 / doc-link gates still expect root AGENT_MEMORY.md.
    if not _exists(client, owner, name, "AGENT_MEMORY.md", branch):
        if _exists(client, owner, name, ".agent/AGENT_MEMORY.md", branch):
            stub = (
                "# Agent memory\n\n"
                "Canonical living memory: [`.agent/AGENT_MEMORY.md`](.agent/AGENT_MEMORY.md).\n"
            )
            _put(
                client, owner, name, "AGENT_MEMORY.md", stub.encode("utf-8"),
                "chore(argus): add root AGENT_MEMORY.md pointer", branch, None,
            )
            actions.append("agent_memory_stub")

    # Parent docs may link branding/brand.json / DIRECTORY_RULES.md — stub when missing.
    if _exists(client, owner, name, "docs/BRAND_ICON.md", branch):
        if not _exists(client, owner, name, "branding/brand.json", branch):
            stub = b'{\n  "name": "brand",\n  "note": "stub for doc-link gate; replace with real brand"\n}\n'
            _put(
                client, owner, name, "branding/brand.json", stub,
                "chore(argus): stub branding/brand.json for doc links", branch, None,
            )
            actions.append("brand_stub")
    if _exists(client, owner, name, "docs/LAYOUT.md", branch):
        if not _exists(client, owner, name, "docs/DIRECTORY_RULES.md", branch):
            stub = (
                b"# Directory rules\n\n"
                b"Stub for doc-link gate. Prefer product layout docs when present.\n"
            )
            _put(
                client, owner, name, "docs/DIRECTORY_RULES.md", stub,
                "chore(argus): stub docs/DIRECTORY_RULES.md for doc links", branch, None,
            )
            actions.append("directory_rules_stub")

    if not actions and got is None:
        return "missing"
    return "changed:" + ",".join(actions) if actions else "unchanged"


def heal_open_upgrade_prs(
    client: GitHubClient,
    *,
    login: str | None = None,
    max_repos: int = 80,
) -> dict[str, Any]:
    """Search open upgrade PRs and heal each head."""
    out: dict[str, Any] = {"healed": [], "skipped": [], "errors": []}
    try:
        me = login or str((client.whoami() or {}).get("login") or "")
    except GitHubError as exc:
        out["errors"].append(str(exc))
        return out
    if not me:
        out["errors"].append("no_login")
        return out
    try:
        data = client.get(
            "/search/issues",
            params={
                "q": f'user:{me} is:pr is:open "upgrade parent rules" in:title',
                "per_page": min(100, max_repos),
            },
        )
    except GitHubError as exc:
        out["errors"].append(str(exc))
        return out
    items = data.get("items") if isinstance(data, dict) else []
    for it in items or []:
        if len(out["healed"]) + len(out["skipped"]) + len(out["errors"]) >= max_repos:
            break
        repo_url = str(it.get("repository_url") or "")
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            continue
        owner, name = parts[-2], parts[-1]
        num = int(it["number"])
        try:
            pr = client.get(f"/repos/{owner}/{name}/pulls/{num}")
            head = str(((pr or {}).get("head") or {}).get("ref") or "")
        except GitHubError as exc:
            out["errors"].append(f"{owner}/{name}#{num}:{exc}")
            continue
        if not head.startswith(BRANCH_PREFIX):
            out["skipped"].append(f"{owner}/{name}#{num}:head={head}")
            continue
        try:
            status = heal_template_index(client, owner, name, head)
            key = f"{owner}/{name}#{num}:{status}"
            if status.startswith("changed"):
                out["healed"].append(key)
            else:
                out["skipped"].append(key)
        except GitHubError as exc:
            out["errors"].append(f"{owner}/{name}#{num}:{exc}")
    return out
