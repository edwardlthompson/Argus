"""PR-only lineage fanout — .template-version (+ missing .template-update.json)."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any

from argus.action_ledger import append_action
from argus.config_loader import load_yaml
from argus.fleet import halt, is_halted
from argus.github_client import GitHubClient, GitHubError
from argus.paths import CONFIG_DIR, PROJECT_ROOT

EXCLUDE = frozenset({
    "edwardlthompson/Argus",
    "edwardlthompson/agent-project-bootstrap",
    "edwardlthompson/edwardlthompson",
    "edwardlthompson/argus-runner",
})
BRANCH = "chore/argus-fleet-template-version"


@dataclass
class FleetApplyResult:
    opened: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    digest: list[str] = field(default_factory=list)


def expected_version() -> str:
    cfg = load_yaml(CONFIG_DIR / "parent.yaml") if (CONFIG_DIR / "parent.yaml").is_file() else {}
    return str(cfg.get("expected_version") or "1.13.0").strip()


def upstream_name() -> str:
    cfg = load_yaml(CONFIG_DIR / "parent.yaml") if (CONFIG_DIR / "parent.yaml").is_file() else {}
    return str(cfg.get("upstream") or "edwardlthompson/agent-project-bootstrap")


def _decode_content(data: dict[str, Any]) -> str:
    raw = data.get("content") or ""
    return base64.b64decode(raw).decode("utf-8", errors="replace").strip()


def read_template_version(client: GitHubClient, full_name: str) -> str | None:
    owner, name = full_name.split("/", 1)
    try:
        data = client.get(f"/repos/{owner}/{name}/contents/.template-version")
    except GitHubError:
        return None
    if not isinstance(data, dict):
        return None
    return _decode_content(data).split()[0] if _decode_content(data) else None


def _ensure_branch(client: GitHubClient, owner: str, name: str, default: str) -> None:
    ref = client.get(f"/repos/{owner}/{name}/git/ref/heads/{default}")
    base_sha = ref["object"]["sha"]
    try:
        client.post(
            f"/repos/{owner}/{name}/git/refs",
            allow_write=True,
            json={"ref": f"refs/heads/{BRANCH}", "sha": base_sha},
        )
    except GitHubError as exc:
        if "422" not in str(exc):
            raise


def _put_file(
    client: GitHubClient,
    owner: str,
    name: str,
    path: str,
    content: str,
    message: str,
) -> None:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload: dict[str, Any] = {"message": message, "content": encoded, "branch": BRANCH}
    try:
        existing = client.get(f"/repos/{owner}/{name}/contents/{path}", params={"ref": BRANCH})
        if isinstance(existing, dict) and existing.get("sha"):
            payload["sha"] = existing["sha"]
    except GitHubError:
        pass
    client.put(f"/repos/{owner}/{name}/contents/{path}", allow_write=True, json=payload)


def open_lineage_pr(client: GitHubClient, full_name: str, *, brief_id: str) -> str:
    """Open PR bumping .template-version only (plus missing update JSON)."""
    if full_name in EXCLUDE:
        raise GitHubError(f"excluded:{full_name}")
    owner, name = full_name.split("/", 1)
    ver = expected_version()
    current = read_template_version(client, full_name)
    if current is None:
        raise GitHubError(f"no_lineage:{full_name}")
    if current == ver:
        raise GitHubError(f"already_current:{full_name}")
    repo = client.get(f"/repos/{owner}/{name}")
    default = str(repo.get("default_branch") or "main")
    _ensure_branch(client, owner, name, default)
    _put_file(
        client, owner, name, ".template-version", ver + "\n",
        f"chore(argus): bump .template-version to {ver}",
    )
    try:
        client.get(f"/repos/{owner}/{name}/contents/.template-update.json")
    except GitHubError:
        body = (
            "{\n"
            f'  "upstream": "{upstream_name()}",\n'
            '  "check_interval": "weekly",\n'
            '  "last_checked": null,\n'
            '  "notify_method": "stdout"\n'
            "}\n"
        )
        _put_file(
            client, owner, name, ".template-update.json", body,
            "chore(argus): add .template-update.json",
        )
    title = f"chore(argus): bump .template-version to {ver}"
    try:
        pr = client.post(
            f"/repos/{owner}/{name}/pulls",
            allow_write=True,
            json={
                "title": title,
                "head": BRANCH,
                "base": default,
                "body": (
                    f"Argus fleet lineage bump (`{brief_id}`).\n\n"
                    f"- `.template-version`: `{current}` → `{ver}`\n"
                    "- No product source changes.\n"
                    "- Parent: `edwardlthompson/agent-project-bootstrap`.\n"
                ),
            },
        )
        url = str(pr.get("html_url") or "")
    except GitHubError as exc:
        if "422" not in str(exc):
            raise
        head = f"{owner}:{BRANCH}"
        existing = client.get(
            f"/repos/{owner}/{name}/pulls",
            params={"state": "open", "head": head, "per_page": 5},
        )
        url = (
            str(existing[0].get("html_url") or f"existing-pr:{head}")
            if isinstance(existing, list) and existing
            else f"existing-pr:{head}"
        )
    append_action(
        actor="fleet",
        repo=full_name,
        action="lineage_pr",
        detail=f"{current}->{ver}",
        pr_url=url if url.startswith("http") else None,
        brief_id=brief_id,
    )
    return url


def apply_wave(
    client: GitHubClient,
    repos: list[str],
    *,
    brief_id: str,
    root=None,
) -> FleetApplyResult:
    result = FleetApplyResult()
    if is_halted(root or PROJECT_ROOT):
        result.errors.append("halted")
        return result
    for full in repos:
        if full in EXCLUDE:
            result.skipped.append(f"{full}:excluded")
            continue
        try:
            url = open_lineage_pr(client, full, brief_id=brief_id)
            result.opened.append(f"{full}:{url}")
        except GitHubError as exc:
            msg = str(exc)
            if msg.startswith("already_current:"):
                result.skipped.append(msg)
            elif msg.startswith("no_lineage:"):
                result.digest.append(f"- `{full}` — no `.template-version` (skipped; not invented)")
                result.skipped.append(msg)
            else:
                result.errors.append(f"{full}:{exc}")
                halt(f"fleet wave failed on {full}: {exc}", root=root or PROJECT_ROOT)
                break
    return result


def pr_checks_green(client: GitHubClient, pr_url: str) -> bool | None:
    """True green, False red, None pending/unknown."""
    try:
        parts = pr_url.rstrip("/").split("/")
        owner, name, num = parts[-4], parts[-3], int(parts[-1])
        pr = client.get(f"/repos/{owner}/{name}/pulls/{num}")
        sha = str(((pr or {}).get("head") or {}).get("sha") or "")
        if not sha:
            return None
        status = client.get(f"/repos/{owner}/{name}/commits/{sha}/status")
        state = str((status or {}).get("state") or "")
        if state == "success":
            return True
        if state in ("failure", "error"):
            return False
        runs = client.get(
            f"/repos/{owner}/{name}/commits/{sha}/check-runs", params={"per_page": 30}
        )
        items = (runs or {}).get("check_runs") if isinstance(runs, dict) else None
        if not items:
            return True
        bad = ("failure", "timed_out", "cancelled", "action_required")
        if any(str(c.get("conclusion") or "") in bad for c in items):
            return False
        if any(str(c.get("status") or "") != "completed" for c in items):
            return None
        return True
    except (IndexError, ValueError, GitHubError):
        return None
