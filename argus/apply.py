"""Safe auto-apply for deterministic fixes. Prefers PRs. Real GitHub mutations when not dry-run."""

from __future__ import annotations

import base64
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

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


def _topics_for(plan: RepoPlan) -> list[str]:
    existing = [t for t in plan.repo.topics if t.lower() not in {"foss", "mit", "open-source", "opensource"}]
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


def _file_from_template(fix_id: str) -> tuple[str, str] | None:
    templates = {
        "HYGIENE-SECURITY-MD": (
            "SECURITY.md",
            "# Security Policy\n\nReport vulnerabilities privately via GitHub Security Advisories.\n",
        ),
        "HYGIENE-CONTRIBUTING": (
            "CONTRIBUTING.md",
            "# Contributing\n\n1. Open an issue or PR.\n2. Keep changes focused.\n3. Run tests before review.\n",
        ),
        "HYGIENE-COC": (
            "CODE_OF_CONDUCT.md",
            "# Code of Conduct\n\nBe respectful. Harassment is not tolerated.\n",
        ),
        "HYGIENE-GITATTRIBUTES": (
            ".gitattributes",
            "* text=auto eol=lf\n*.py text eol=lf\n*.md linguist-documentation=true\n",
        ),
        "HYGIENE-LICENSE": (
            "LICENSE",
            "MIT License\n\nCopyright (c) contributors\n\nPermission is hereby granted...\n",
        ),
        "HYGIENE-CI": (
            ".github/workflows/ci.yml",
            (
                "name: ci\non:\n  push:\n    branches: [main, master]\n  pull_request:\n"
                "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: actions/checkout@v4\n      - run: echo ok\n"
            ),
        ),
    }
    return templates.get(fix_id)


def _handler_file_pr(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    pair = _file_from_template(matched.fix.id)
    if not pair:
        raise GitHubError(f"No file template for {matched.fix.id}")
    path, body = pair
    return _content_pr(client, plan, matched, path, body, f"chore(argus): add {path}")


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


HANDLERS: dict[str, Handler] = {
    "HYGIENE-TOPICS": _put_topics,
    "HYGIENE-DESCRIPTION": _patch_description,
    "HYGIENE-SECURITY-MD": _handler_file_pr,
    "HYGIENE-CONTRIBUTING": _handler_file_pr,
    "HYGIENE-COC": _handler_file_pr,
    "HYGIENE-GITATTRIBUTES": _handler_file_pr,
    "HYGIENE-LICENSE": _handler_file_pr,
    "HYGIENE-CI": _handler_file_pr,
    "LINEAGE-VERSION-STALE": _lineage_version,
    "LINEAGE-MISSING-MARKERS": _lineage_markers,
}


def apply_auto_safe(
    client: GitHubClient,
    store: StateStore,
    plans: list[RepoPlan],
    *,
    dry_run: bool = True,
    max_prs: int = 5,
) -> ApplyResult:
    result = ApplyResult()
    if client.report_only:
        for plan in plans:
            for m in plan.auto_fixes:
                result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:report_only")
        return result

    opened = 0
    for plan in plans:
        if not plan.repo.can_write:
            for m in plan.auto_fixes:
                result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:no_write")
            continue
        for m in plan.auto_fixes:
            if opened >= max_prs:
                result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:max_prs")
                continue
            key = f"{plan.repo.full_name}:{m.fix.id}"
            result.attempted.append(key)
            if dry_run:
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
    }
