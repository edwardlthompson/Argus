"""Safe auto-apply for deterministic fixes. Prefers PRs. Real GitHub mutations when not dry-run."""

from __future__ import annotations

import base64
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from argus.apply_templates import file_from_template
from argus.config_loader import load_yaml
from argus.github_client import GitHubClient, GitHubError
from argus.models import MatchedFix, RepoPlan
from argus.paths import CONFIG_DIR
from argus.state import StateStore

Handler = Callable[[GitHubClient, RepoPlan, MatchedFix], str]


@dataclass
class ApplyResult:
    attempted: list[str] = field(default_factory=list)
    opened_prs: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    would_prs: list[dict[str, str]] = field(default_factory=list)


def _banned_topics() -> set[str]:
    path = CONFIG_DIR / "topics.yaml"
    if not path.exists():
        return {"foss", "mit", "open-source", "opensource"}
    data = load_yaml(path) or {}
    return {str(t).lower() for t in (data.get("generic") or [])}


def _topics_for(plan: RepoPlan) -> list[str]:
    banned = _banned_topics()
    existing = [t for t in plan.repo.topics if t.lower() not in banned]
    name_bits = re.split(r"[^a-z0-9]+", plan.repo.name.lower())
    for bit in name_bits:
        if len(bit) >= 3 and bit not in existing:
            existing.append(bit)
        if len(existing) >= 5:
            break
    while len(existing) < 3:
        existing.append(f"project-{len(existing)+1}")
    return existing[:5]


def _put_topics(client: GitHubClient, plan: RepoPlan, _m: MatchedFix) -> str:
    topics = _topics_for(plan)
    client.put(
        f"/repos/{plan.repo.owner}/{plan.repo.name}/topics",
        allow_write=True,
        json={"names": topics},
    )
    return f"topics:{','.join(topics)}"


def _patch_description(client: GitHubClient, plan: RepoPlan, _m: MatchedFix) -> str:
    desc = (plan.repo.description or "")[:120]
    client.patch(
        f"/repos/{plan.repo.owner}/{plan.repo.name}",
        allow_write=True,
        json={"description": desc},
    )
    return f"description:{len(desc)}"


def _content_pr(
    client: GitHubClient,
    plan: RepoPlan,
    matched: MatchedFix,
    path: str,
    content: str,
    message: str,
) -> str:
    owner, name = plan.repo.owner, plan.repo.name
    branch = f"chore/argus-{matched.fix.id.lower()}"
    repo = client.get(f"/repos/{owner}/{name}")
    default = repo.get("default_branch") or "main"
    ref = client.get(f"/repos/{owner}/{name}/git/ref/heads/{default}")
    base_sha = ref["object"]["sha"]
    try:
        client.post(
            f"/repos/{owner}/{name}/git/refs",
            allow_write=True,
            json={"ref": f"refs/heads/{branch}", "sha": base_sha},
        )
    except GitHubError as exc:
        if "422" not in str(exc):
            raise
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload: dict[str, Any] = {
        "message": message,
        "content": encoded,
        "branch": branch,
    }
    try:
        existing = client.get(f"/repos/{owner}/{name}/contents/{path}", params={"ref": branch})
        if isinstance(existing, dict) and existing.get("sha"):
            payload["sha"] = existing["sha"]
    except GitHubError:
        pass
    client.put(
        f"/repos/{owner}/{name}/contents/{path}",
        allow_write=True,
        json=payload,
    )
    try:
        pr = client.post(
            f"/repos/{owner}/{name}/pulls",
            allow_write=True,
            json={
                "title": f"chore(argus): {matched.fix.title}",
                "head": branch,
                "base": default,
                "body": (
                    f"Argus auto-safe `{matched.fix.id}`\n\n"
                    f"**Why:** {matched.fix.why}\n\n"
                    f"**Gate:** `{matched.fix.gate}`\n"
                ),
            },
        )
        return str(pr.get("html_url") or "")
    except GitHubError as exc:
        if "422" not in str(exc):
            raise
        # PR already open for this Argus branch — treat as success.
        head = f"{owner}:{branch}"
        existing = client.get(
            f"/repos/{owner}/{name}/pulls",
            params={"state": "open", "head": head, "per_page": 5},
        )
        if isinstance(existing, list) and existing:
            return str(existing[0].get("html_url") or f"existing-pr:{head}")
        return f"existing-pr:{head}"


def _handler_file_pr(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    pair = file_from_template(matched.fix.id)
    if not pair:
        raise GitHubError(f"No file template for {matched.fix.id}")
    path, body = pair
    if matched.fix.id == "HYGIENE-CODEOWNERS":
        body = body.replace("@OWNER", f"@{plan.repo.owner}")
    return _content_pr(client, plan, matched, path, body, f"chore(argus): add {path}")


def _enable_dependabot(client: GitHubClient, plan: RepoPlan, _m: MatchedFix) -> str:
    client.put(
        f"/repos/{plan.repo.owner}/{plan.repo.name}/vulnerability-alerts",
        allow_write=True,
    )
    return f"dependabot-alerts:{plan.repo.full_name}"


def _enable_secret_scanning(client: GitHubClient, plan: RepoPlan, _m: MatchedFix) -> str:
    client.patch(
        f"/repos/{plan.repo.owner}/{plan.repo.name}",
        allow_write=True,
        json={
            "security_and_analysis": {
                "secret_scanning": {"status": "enabled"},
                "secret_scanning_push_protection": {"status": "enabled"},
            }
        },
    )
    return f"secret-scanning:{plan.repo.full_name}"


def _lineage_version(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    cfg = load_yaml(CONFIG_DIR / "parent.yaml") if (CONFIG_DIR / "parent.yaml").exists() else {}
    expected = str(cfg.get("expected_version", "1.12.0"))
    return _content_pr(
        client,
        plan,
        matched,
        ".template-version",
        expected + "\n",
        f"chore(argus): bump .template-version to {expected}",
    )


def _lineage_markers(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    cfg = load_yaml(CONFIG_DIR / "parent.yaml") if (CONFIG_DIR / "parent.yaml").exists() else {}
    expected = str(cfg.get("expected_version", "1.12.0"))
    upstream = str(cfg.get("upstream", "edwardlthompson/agent-project-bootstrap"))
    urls: list[str] = []
    urls.append(
        _content_pr(
            client,
            plan,
            matched,
            ".template-version",
            expected + "\n",
            "chore(argus): add .template-version",
        )
    )
    body = (
        '{\n'
        f'  "upstream": "{upstream}",\n'
        '  "check_interval": "weekly",\n'
        '  "last_checked": null,\n'
        '  "notify_method": "stdout"\n'
        "}\n"
    )
    # Second file on same branch — reuse branch name via fix id
    urls.append(
        _content_pr(
            client,
            plan,
            matched,
            ".template-update.json",
            body,
            "chore(argus): add .template-update.json",
        )
    )
    return urls[-1]


def _read_repo_text(client: GitHubClient, plan: RepoPlan, path: str) -> str | None:
    try:
        data = client.get(f"/repos/{plan.repo.owner}/{plan.repo.name}/contents/{path}")
    except GitHubError:
        return None
    if not isinstance(data, dict) or not data.get("content"):
        return None
    try:
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except (TypeError, ValueError):
        return None


def _locate_board(client: GitHubClient, plan: RepoPlan) -> tuple[str | None, str | None]:
    from argus.board_classify import locate_board_path

    root = _read_repo_text(client, plan, "BUILD_PLAN.md")
    docs = None if root is not None else _read_repo_text(client, plan, "docs/BUILD_PLAN.md")
    path = locate_board_path(root_exists=root is not None, docs_exists=docs is not None)
    return path, (root if root is not None else docs)


def _board_markers(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    from argus.board_normalize import append_missing_markers

    path, text = _locate_board(client, plan)
    if not path or text is None:
        return f"board-missing:{plan.repo.full_name}"
    updated = append_missing_markers(text)
    if updated == text:
        return f"board-markers-ok:{plan.repo.full_name}"
    return _content_pr(
        client,
        plan,
        matched,
        path,
        updated,
        "chore(argus): add BUILD_PLAN marker lanes",
    )


def _board_restructure(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    from argus.board_normalize import restructure_divergent

    path, text = _locate_board(client, plan)
    if not path or text is None:
        return f"board-missing:{plan.repo.full_name}"
    has_completed = _read_repo_text(client, plan, "COMPLETED_TASKS.md") is not None or (
        _read_repo_text(client, plan, "docs/COMPLETED_TASKS.md") is not None
    )
    files = restructure_divergent(text, source_path=path, has_completed_tasks=has_completed)
    url = ""
    for fpath, body in files.items():
        url = _content_pr(
            client,
            plan,
            matched,
            fpath,
            body,
            "chore(argus): normalize BUILD_PLAN to APB format",
        )
    return url or f"board-restructure:{plan.repo.full_name}"


HANDLERS: dict[str, Handler] = {
    "HYGIENE-TOPICS": _put_topics,
    "HYGIENE-DESCRIPTION": _patch_description,
    "HYGIENE-SECURITY-MD": _handler_file_pr,
    "HYGIENE-CONTRIBUTING": _handler_file_pr,
    "HYGIENE-COC": _handler_file_pr,
    "HYGIENE-GITATTRIBUTES": _handler_file_pr,
    "HYGIENE-LICENSE": _handler_file_pr,
    "HYGIENE-CI": _handler_file_pr,
    "HYGIENE-CODEOWNERS": _handler_file_pr,
    "HYGIENE-GITIGNORE": _handler_file_pr,
    "SEC-CODEQL-WORKFLOW": _handler_file_pr,
    "SEC-DEPENDABOT-ENABLE": _enable_dependabot,
    "SEC-SECRET-SCAN-ENABLE": _enable_secret_scanning,
    "LINEAGE-VERSION-STALE": _lineage_version,
    "LINEAGE-MISSING-MARKERS": _lineage_markers,
    "BOARD-MARKERS": _board_markers,
}


def apply_auto_safe(
    client: GitHubClient,
    store: StateStore,
    plans: list[RepoPlan],
    *,
    dry_run: bool = True,
    max_prs: int = 5,
    max_prs_per_owner: int | None = None,
) -> ApplyResult:
    result = ApplyResult()
    if client.report_only:
        for plan in plans:
            for m in plan.auto_fixes:
                result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:report_only")
        return result

    opened = 0
    per_owner: dict[str, int] = {}
    for plan in plans:
        if not plan.repo.can_write:
            for m in plan.auto_fixes:
                result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:no_write")
            continue
        for m in plan.auto_fixes:
            owner = plan.repo.owner
            if opened >= max_prs:
                result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:max_prs")
                continue
            if max_prs_per_owner is not None and per_owner.get(owner, 0) >= max_prs_per_owner:
                result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:max_owner")
                continue
            key = f"{plan.repo.full_name}:{m.fix.id}"
            result.attempted.append(key)
            preview = file_from_template(m.fix.id)
            path_hint = preview[0] if preview else m.fix.id
            if dry_run:
                result.would_prs.append(
                    {"repo": plan.repo.full_name, "fix": m.fix.id, "path": path_hint}
                )
                result.skipped.append(f"{key}:dry_run")
                continue
            handler = HANDLERS.get(m.fix.id)
            if not handler:
                result.skipped.append(f"{key}:no_handler")
                continue
            try:
                url = handler(client, plan, m)
                result.opened_prs.append(url)
                result.applied.append(key)
                ttl = m.fix.resolution_ttl_days or 30
                store.record_resolution(
                    plan.repo.full_name, m.fix.id, ttl_days=ttl, source="auto_apply"
                )
                opened += 1
                per_owner[owner] = per_owner.get(owner, 0) + 1
            except GitHubError as exc:
                result.errors.append(f"{key}:{exc}")
    return result


def summarize_apply(result: ApplyResult) -> dict[str, Any]:
    return {
        "attempted": result.attempted,
        "opened_prs": result.opened_prs,
        "skipped": result.skipped,
        "errors": result.errors,
        "applied": result.applied,
        "would_prs": result.would_prs,
    }
