"""Plan and (optionally) open tag-only release-prep PRs. Never tags or publishes."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord
from argus.paths import CONFIG_DIR
from argus.release_detect import bump_version_text, cfg


@dataclass
class PrepPlan:
    repo: str
    branch: str
    title: str
    body: str
    files: dict[str, str] = field(default_factory=dict)
    irregular: bool = False
    existing_pr: str | None = None
    tag_cmd: str = ""


def _render(name: str, row: dict[str, Any], config: dict[str, Any]) -> str:
    desk = config.get("desktop") or {}
    key = "private_os" if row.get("private") else "public_os"
    os_list = ", ".join(str(x) for x in (desk.get(key) or ["ubuntu-latest"]))
    text = (CONFIG_DIR / "release_workflows" / name).read_text(encoding="utf-8")
    workdir = str(row.get("electron_workdir") or ".")
    slug = str(row.get("name") or "app").lower()
    return text.replace("__OS_LIST__", os_list).replace("__WORKDIR__", workdir).replace("__APP_SLUG__", slug)


def _changelog(old: str, version: str) -> str:
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    note = f"## [{version}] — {day}\n\n- Release prep: attach artifacts on the `v*` tag.\n"
    if not old.strip():
        return f"# Changelog\n\n## [Unreleased]\n\n{note}\n"
    if "## [Unreleased]" in old:
        return old.replace("## [Unreleased]", f"## [Unreleased]\n\n{note}".rstrip("\n"), 1)
    return note + "\n" + old


def _body(row: dict[str, Any], files: dict[str, str], config: dict[str, Any]) -> str:
    tag = row.get("next_tag") or "v0.1.0"
    last = row.get("latest_tag") or "none"
    if row.get("latest_date"):
        last = f"{last} ({row['latest_date']})"
    macos = ""
    plats = config.get("platforms") or {}
    desktop = any((plats.get(p) or {}).get("template") == "desktop.yml" for p in row.get("platforms") or [])
    if row.get("private") and desktop:
        macos = "\nThis repo is **private** — macOS runners omitted (10× billed minutes).\n"
    return (
        f"Argus release-prep (`RELEASE-PREP`)\n\n**Platforms:** {', '.join(row.get('platforms') or []) or '—'}\n"
        f"**Last release:** {last}\n**What's missing:** {'; '.join(row.get('missing') or []) or 'release hygiene'}\n"
        f"**Files:** {', '.join(files) or 'none'}\n{macos}\n"
        f"Argus never creates tags or GitHub Releases. After merge, cut the tag yourself:\n\n"
        f"```bash\ngit tag -a {tag} -m \"{tag}\" && git push origin {tag}\n```\n\n"
        f"Workflows trigger only on `v*` tag push and `workflow_dispatch` (never branch push/PR).\n"
    )


def plan_prep(row: dict[str, Any], config: dict[str, Any] | None = None) -> PrepPlan:
    c = cfg(config)
    branch = str(c.get("branch") or "chore/argus-release-prep")
    if row.get("irregular") or not row.get("needs_prep"):
        return PrepPlan(repo=row["full_name"], branch=branch, title="", body="", irregular=bool(row.get("irregular")))
    files: dict[str, str] = {}
    existing = {str(p).lower() for p in (row.get("workflow_paths") or [])}
    for pid in row.get("platforms") or []:
        rule = (c.get("platforms") or {}).get(pid) or {}
        tmpl = rule.get("template")
        if not tmpl or rule.get("irregular"):
            continue
        dest = f".github/workflows/release-{pid}.yml"
        if dest.lower() in existing or any(pid in p and "release" in p for p in existing):
            continue
        files[dest] = _render(str(tmpl), row, c)
    kind, path = row.get("version_kind"), row.get("version_path")
    text, ver = row.get("source_text"), row.get("next_version")
    if kind and path and text and ver:
        updated = bump_version_text(text, str(kind), str(ver))
        if updated != text:
            files[path] = updated
    files["CHANGELOG.md"] = _changelog(row.get("changelog_text") or "", str(ver or row.get("next_version") or "0.1.0"))
    body = _body(row, files, c)
    title = str((c.get("pr") or {}).get("title") or "chore(argus): release-prep")
    return PrepPlan(
        repo=row["full_name"], branch=branch, title=title, body=body, files=files,
        tag_cmd=f'git tag -a {row.get("next_tag")} -m "{row.get("next_tag")}" && git push origin {row.get("next_tag")}',
    )


def find_existing_pr(client: GitHubClient, repo: RepoRecord, branch: str) -> dict[str, Any] | None:
    try:
        pulls = client.get(f"/repos/{repo.owner}/{repo.name}/pulls", params={"state": "open", "per_page": 30})
    except GitHubError:
        pulls = []
    for pr in pulls if isinstance(pulls, list) else []:
        head = str((pr.get("head") or {}).get("ref") or "")
        if head == branch or "release-prep" in str(pr.get("title") or "").lower():
            return pr if isinstance(pr, dict) else None
    return None


def _put_file(client: GitHubClient, repo: RepoRecord, branch: str, path: str, content: str, message: str) -> None:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload: dict[str, Any] = {"message": message, "content": encoded, "branch": branch}
    try:
        existing = client.get(f"/repos/{repo.owner}/{repo.name}/contents/{path}", params={"ref": branch})
        if isinstance(existing, dict) and existing.get("sha"):
            payload["sha"] = existing["sha"]
    except GitHubError:
        pass
    client.put(f"/repos/{repo.owner}/{repo.name}/contents/{path}", allow_write=True, json=payload)


def apply_prep(client: GitHubClient, repo: RepoRecord, plan: PrepPlan, *, dry_run: bool) -> dict[str, str]:
    if plan.irregular or not plan.files:
        return {"action": "skipped", "reason": "irregular" if plan.irregular else "no_files"}
    existing = find_existing_pr(client, repo, plan.branch)
    url = str((existing or {}).get("html_url") or "")
    if dry_run:
        return {"action": "would_update" if existing else "would_open", "pr": url}
    default = str(client.get(f"/repos/{repo.owner}/{repo.name}").get("default_branch") or "main")
    sha = client.get(f"/repos/{repo.owner}/{repo.name}/git/ref/heads/{default}")["object"]["sha"]
    try:
        client.post(f"/repos/{repo.owner}/{repo.name}/git/refs", allow_write=True,
                    json={"ref": f"refs/heads/{plan.branch}", "sha": sha})
    except GitHubError as exc:
        if "422" not in str(exc):
            raise
    for path, body in plan.files.items():
        _put_file(client, repo, plan.branch, path, body, f"chore(argus): release-prep {path}")
    if existing:
        return {"action": "updated", "pr": url}
    try:
        pr = client.post(f"/repos/{repo.owner}/{repo.name}/pulls", allow_write=True,
                         json={"title": plan.title, "head": plan.branch, "base": default, "body": plan.body})
        return {"action": "opened", "pr": str(pr.get("html_url") or "")}
    except GitHubError as exc:
        if "422" not in str(exc):
            raise
        found = find_existing_pr(client, repo, plan.branch) or {}
        return {"action": "existing", "pr": str(found.get("html_url") or "")}
