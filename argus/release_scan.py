"""GitHub REST collection for `argus releases` (local CLI — not Actions)."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Any

import yaml

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord
from argus.release_detect import cfg, evaluate, extract_version, hot_triggers, match_platforms


def _read(client: GitHubClient, repo: RepoRecord, path: str) -> str | None:
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
    except GitHubError:
        return None
    if not isinstance(data, dict) or not data.get("content"):
        return None
    try:
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except (TypeError, ValueError):
        return None


def _paths(client: GitHubClient, repo: RepoRecord) -> list[str]:
    try:
        tree = client.get(
            f"/repos/{repo.owner}/{repo.name}/git/trees/{repo.default_branch}",
            params={"recursive": "1"},
        )
    except GitHubError:
        return []
    return [str(n["path"]) for n in (tree.get("tree") or []) if n.get("type") == "blob" and n.get("path")]


def _days_since(iso: str | None) -> int | None:
    if not iso:
        return None
    dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    return max(0, (datetime.now(UTC) - dt).days)


def collect_repo(client: GitHubClient, repo: RepoRecord, config: dict[str, Any] | None = None) -> dict[str, Any]:
    c = cfg(config)
    paths = _paths(client, repo)
    platforms = match_platforms(paths, c)
    latest = tag = published = assets = None
    try:
        rels = client.get(f"/repos/{repo.owner}/{repo.name}/releases", params={"per_page": 1})
        if isinstance(rels, list) and rels:
            latest = rels[0]
            tag, published = latest.get("tag_name"), latest.get("published_at") or latest.get("created_at")
            assets = [str(a.get("name") or "") for a in (latest.get("assets") or [])]
    except GitHubError:
        pass
    ahead = 0
    if tag:
        try:
            cmp_ = client.get(f"/repos/{repo.owner}/{repo.name}/compare/{tag}...{repo.default_branch}")
            ahead = int((cmp_ or {}).get("ahead_by") or 0)
        except GitHubError:
            if published:
                try:
                    commits = client.get(
                        f"/repos/{repo.owner}/{repo.name}/commits",
                        params={"sha": repo.default_branch, "since": published, "per_page": 1},
                    )
                    ahead = 1 if commits else 0
                except GitHubError:
                    ahead = 0
    wf_paths = [p for p in paths if p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml"))]
    workflows, tag_release = [], False
    for path in wf_paths[:25]:
        text = _read(client, repo, path) or ""
        try:
            data = yaml.safe_load(text) or {}
        except yaml.YAMLError:
            data = {}
        on = data.get("on") if isinstance(data, dict) else None
        if on is None and isinstance(data, dict):
            on = data.get(True)
        hot = hot_triggers(on)
        events = on if isinstance(on, dict) else {}
        tags_only = isinstance(events.get("push"), dict) and bool((events.get("push") or {}).get("tags"))
        low = path.lower() + " " + str(data.get("name") or "").lower()
        named = "release" in low and "release-please" not in low
        if tags_only and not hot:
            tag_release = True
        workflows.append({
            "path": path, "name": data.get("name") if isinstance(data, dict) else path,
            "hot": hot, "tags_only": bool(tags_only), "named_release": named,
        })
    source_ver = source_path = source_text = kind = None
    for pid in platforms:
        rule = (c.get("platforms") or {}).get(pid) or {}
        kind = rule.get("version_kind")
        for vf in rule.get("version_files") or []:
            if vf in paths:
                source_text = _read(client, repo, vf)
                source_ver = extract_version(source_text or "", str(kind or ""))
                source_path = vf
                break
        if source_path:
            break
    changelog = _read(client, repo, "CHANGELOG.md") if "CHANGELOG.md" in paths else None
    facts: dict[str, Any] = {
        "full_name": repo.full_name, "owner": repo.owner, "name": repo.name,
        "status": repo.status.value, "private": repo.private, "fork": repo.fork,
        "language": (repo.raw or {}).get("language"), "topics": list(repo.topics),
        "html_url": repo.html_url, "default_branch": repo.default_branch,
        "platforms": platforms, "has_release": bool(latest), "latest_tag": tag,
        "latest_date": str(published)[:10] if published else None,
        "days_since_release": _days_since(published), "ahead_by": ahead,
        "asset_names": assets or [], "has_tag_release_workflow": tag_release,
        "workflows": workflows, "workflow_paths": wf_paths,
        "source_version": source_ver, "version_path": source_path, "version_kind": kind,
        "source_text": source_text, "changelog_text": changelog,
        "electron_workdir": "electron" if "electron/package.json" in paths else ".",
        "visibility": "private" if repo.private else "public",
        "irregular_reason": (
            "hot_release_workflow"
            if any(w.get("named_release") and w.get("hot") for w in workflows)
            else None
        ),
    }
    facts.update(evaluate(facts, c))
    return facts
