"""YOLO: auto-merge Argus PRs + API-automate selected human/agent fixes."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from argus.apply import _content_pr, _lineage_version
from argus.github_client import GitHubClient, GitHubError
from argus.models import MatchedFix, RepoPlan
from argus.profile_icon_gen import generate_icon_png
from argus.state import StateStore

_VERSION_BUMP_RE = re.compile(
    r"from\s+v?(\d+)\.(\d+)\.(\d+)\s+to\s+v?(\d+)\.(\d+)\.(\d+)",
    re.I,
)


@dataclass
class YoloResult:
    merged: list[str] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    opened_prs: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    digest_notes: list[str] = field(default_factory=list)


def is_yolo_closable_stale_pr(head_ref: str, author_login: str) -> bool:
    """True when YOLO may close a stale PR (bot / Argus chore head only)."""
    login = (author_login or "").lower()
    ref = head_ref or ""
    return (
        ref.startswith("chore/argus-")
        or "dependabot" in login
        or login.endswith("[bot]")
    )


def is_dependabot_patch_title(title: str, user_login: str | None = None) -> bool:
    """True for Dependabot patch/minor bumps; false for majors or unrelated PRs."""
    t = title or ""
    login = (user_login or "").lower()
    is_bot = "dependabot" in t.lower() or "dependabot" in login
    if not is_bot:
        return False
    if re.search(r"\bmajor\b", t, re.I):
        return False
    m = _VERSION_BUMP_RE.search(t)
    if m:
        a_maj, a_min = int(m.group(1)), int(m.group(2))
        b_maj, b_min = int(m.group(4)), int(m.group(5))
        if b_maj > a_maj:
            return False
        return b_maj == a_maj and b_min >= a_min
    return bool(re.search(r"\b(patch|minor)\b", t, re.I))


def _binary_pr(
    client: GitHubClient,
    plan: RepoPlan,
    matched: MatchedFix,
    path: str,
    raw: bytes,
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
    payload: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": branch,
    }
    try:
        existing = client.get(f"/repos/{owner}/{name}/contents/{path}", params={"ref": branch})
        if isinstance(existing, dict) and existing.get("sha"):
            payload["sha"] = existing["sha"]
    except GitHubError:
        pass
    client.put(f"/repos/{owner}/{name}/contents/{path}", allow_write=True, json=payload)
    try:
        pr = client.post(
            f"/repos/{owner}/{name}/pulls",
            allow_write=True,
            json={
                "title": f"chore(argus): {matched.fix.title}",
                "head": branch,
                "base": default,
                "body": f"Argus YOLO `{matched.fix.id}`\n\n**Why:** {matched.fix.why}\n",
            },
        )
        return str(pr.get("html_url") or "")
    except GitHubError as exc:
        if "422" not in str(exc):
            raise
        return f"existing-pr:{owner}:{branch}"


def _sec_codeql(client: GitHubClient, plan: RepoPlan, _m: MatchedFix) -> str:
    client.put(
        f"/repos/{plan.repo.owner}/{plan.repo.name}/code-scanning/default-setup",
        allow_write=True,
        json={"state": "configured"},
    )
    return f"codeql-default:{plan.repo.full_name}"


def _dependabot_security_updates(client: GitHubClient, plan: RepoPlan, _m: MatchedFix) -> str:
    client.put(
        f"/repos/{plan.repo.owner}/{plan.repo.name}/automated-security-fixes",
        allow_write=True,
    )
    return f"automated-security-fixes:{plan.repo.full_name}"


def _brand_icon(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    png = generate_icon_png(plan.repo.name, plan.repo.description)
    return _binary_pr(
        client,
        plan,
        matched,
        "branding/assets/app-icon-512.png",
        png,
        "chore(argus): add canonical app-icon-512.png",
    )


def _what_not(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    path = "README.md"
    try:
        data = client.get(f"/repos/{plan.repo.owner}/{plan.repo.name}/contents/{path}")
        raw = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except GitHubError:
        raw = f"# {plan.repo.name}\n"
    if "what this is not" in raw.lower():
        return f"what-not-exists:{plan.repo.full_name}"
    section = (
        "\n\n## What this is not\n\n"
        "- A finished commercial product promise\n"
        "- A place for secrets or production credentials\n"
        "- An unbounded scope — see README goals above\n"
    )
    return _content_pr(
        client, plan, matched, path, raw.rstrip() + section + "\n",
        "chore(argus): add What this is not",
    )


def _memory_layout(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    owner, name = plan.repo.owner, plan.repo.name
    try:
        data = client.get(f"/repos/{owner}/{name}/contents/AGENT_MEMORY.md")
    except GitHubError:
        return f"no-root-memory:{plan.repo.full_name}"
    body = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    url = _content_pr(
        client, plan, matched, ".agent/AGENT_MEMORY.md", body,
        "chore(argus): move AGENT_MEMORY.md into .agent/",
    )
    branch = f"chore/argus-{matched.fix.id.lower()}"
    try:
        client._request(  # noqa: SLF001
            "DELETE",
            f"/repos/{owner}/{name}/contents/AGENT_MEMORY.md",
            allow_write=True,
            json={
                "message": "chore(argus): remove root AGENT_MEMORY.md after move",
                "sha": data.get("sha"),
                "branch": branch,
            },
        )
    except GitHubError:
        pass
    return url


def _pr_stale(
    client: GitHubClient,
    plan: RepoPlan,
    matched: MatchedFix,
    *,
    idle_days: int = 30,
) -> str:
    owner, name = plan.repo.owner, plan.repo.name
    pulls = client.get(
        f"/repos/{owner}/{name}/pulls",
        params={"state": "open", "per_page": 30, "sort": "updated", "direction": "asc"},
    )
    if not isinstance(pulls, list):
        return f"pr-stale-none:{plan.repo.full_name}"
    cutoff = datetime.now(UTC) - timedelta(days=max(1, idle_days))
    closed = commented = 0
    for pr in pulls:
        updated = str(pr.get("updated_at") or "")
        try:
            when = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when > cutoff:
            continue
        num = int(pr["number"])
        head_ref = str((pr.get("head") or {}).get("ref") or "")
        login = str((pr.get("user") or {}).get("login") or "").lower()
        if is_yolo_closable_stale_pr(head_ref, login):
            client.patch(
                f"/repos/{owner}/{name}/pulls/{num}",
                allow_write=True,
                json={"state": "closed"},
            )
            closed += 1
        else:
            marker = "<!-- argus:yolo-stale-nudge -->"
            comments = client.get(
                f"/repos/{owner}/{name}/issues/{num}/comments",
                params={"per_page": 30},
            )
            already = False
            if isinstance(comments, list):
                already = any(marker in str(c.get("body") or "") for c in comments)
            if not already:
                client.post(
                    f"/repos/{owner}/{name}/issues/{num}/comments",
                    allow_write=True,
                    json={
                        "body": (
                            f"{marker}\nArgus YOLO: this PR looks idle (≥{idle_days} days). "
                            "Please merge, close, or reply — Argus will not auto-close human PRs."
                        )
                    },
                )
                commented += 1
    return f"pr-stale:{plan.repo.full_name}:closed={closed}:nudged={commented}"


YOLO_HANDLERS = {
    "SEC-CODEQL": _sec_codeql,
    "SEC-OPEN-DEPENDABOT-ALERTS": _dependabot_security_updates,
    "BRAND-ICON-MISSING": _brand_icon,
    "LINEAGE-RECOMMEND-UPGRADE": _lineage_version,
    "AGENT-WHAT-NOT": _what_not,
    "AGENT-MEMORY-LAYOUT": _memory_layout,
}


def apply_yolo_extras(
    client: GitHubClient,
    store: StateStore,
    plans: list[RepoPlan],
    *,
    dry_run: bool,
    max_actions: int,
    yolo_cfg: dict[str, Any] | None = None,
) -> YoloResult:
    """Run YOLO handlers for human + agent fixes that have API automation."""
    cfg = yolo_cfg or {}
    idle = int(cfg.get("stale_pr_idle_days") or cfg.get("close_stale_bot_prs_days") or 30)
    result = YoloResult()
    if client.report_only or dry_run:
        for plan in plans:
            for m in (*plan.human_fixes, *plan.agent_fixes):
                if m.fix.id in YOLO_HANDLERS or m.fix.id == "PR-STALE":
                    result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:dry_run")
        return result
    n = 0
    for plan in plans:
        if not plan.repo.can_write:
            continue
        for m in list(plan.human_fixes) + list(plan.agent_fixes):
            if m.fix.id in ("CI-LATEST-FAILED", "HUMAN-PARK-INACTIVE", "HUMAN-ARCHIVE-JUDGMENT"):
                result.digest_notes.append(
                    f"- `{plan.repo.full_name}` · `{m.fix.id}` — {m.fix.title}"
                )
                store.record_resolution(
                    plan.repo.full_name, m.fix.id, ttl_days=7, source="yolo_digest"
                )
                result.applied.append(f"{plan.repo.full_name}:{m.fix.id}")
                n += 1
                continue
            if m.fix.id == "PR-STALE":
                handler = None
            else:
                handler = YOLO_HANDLERS.get(m.fix.id)
            if m.fix.id != "PR-STALE" and not handler:
                continue
            if n >= max_actions:
                result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:max_actions")
                continue
            key = f"{plan.repo.full_name}:{m.fix.id}"
            try:
                if m.fix.id == "PR-STALE":
                    url = _pr_stale(client, plan, m, idle_days=idle)
                else:
                    assert handler is not None
                    url = handler(client, plan, m)
                result.applied.append(key)
                result.opened_prs.append(url)
                store.record_resolution(
                    plan.repo.full_name, m.fix.id,
                    ttl_days=m.fix.resolution_ttl_days or 30, source="yolo",
                )
                n += 1
            except GitHubError as exc:
                result.errors.append(f"{key}:{exc}")
    return result


def merge_argus_prs(
    client: GitHubClient,
    *,
    max_merges: int,
    login: str | None = None,
) -> YoloResult:
    """Squash-merge open PRs titled chore(argus) for the authenticated user."""
    result = YoloResult()
    if client.report_only:
        result.skipped.append("report_only")
        return result
    try:
        me = login or str((client.whoami() or {}).get("login") or "")
    except GitHubError as exc:
        result.errors.append(str(exc))
        return result
    if not me:
        result.errors.append("no_login")
        return result
    try:
        data = client.get(
            "/search/issues",
            params={
                "q": f"user:{me} is:pr is:open chore/argus in:title",
                "per_page": min(100, max_merges),
            },
        )
    except GitHubError as exc:
        result.errors.append(str(exc))
        return result
    items = data.get("items") if isinstance(data, dict) else []
    for it in items or []:
        if len(result.merged) >= max_merges:
            break
        repo_url = str(it.get("repository_url") or "")
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            continue
        owner, name = parts[-2], parts[-1]
        num = int(it["number"])
        title = str(it.get("title") or "chore(argus)")
        try:
            client.put(
                f"/repos/{owner}/{name}/pulls/{num}/merge",
                allow_write=True,
                json={"merge_method": "squash", "commit_title": title},
            )
            result.merged.append(f"{owner}/{name}#{num}")
        except GitHubError as exc:
            result.errors.append(f"{owner}/{name}#{num}:{exc}")
    return result


def merge_dependabot_patch_prs(
    client: GitHubClient,
    *,
    max_merges: int,
    login: str | None = None,
) -> YoloResult:
    """Squash-merge open Dependabot patch/minor PRs for the user portfolio."""
    result = YoloResult()
    if client.report_only:
        result.skipped.append("report_only")
        return result
    try:
        me = login or str((client.whoami() or {}).get("login") or "")
    except GitHubError as exc:
        result.errors.append(str(exc))
        return result
    if not me:
        result.errors.append("no_login")
        return result
    try:
        data = client.get(
            "/search/issues",
            params={
                "q": f"user:{me} is:pr is:open author:app/dependabot",
                "per_page": min(50, max_merges),
            },
        )
    except GitHubError as exc:
        result.errors.append(str(exc))
        return result
    items = data.get("items") if isinstance(data, dict) else []
    for it in items or []:
        if len(result.merged) >= max_merges:
            break
        title = str(it.get("title") or "")
        user = ((it.get("user") or {}) if isinstance(it.get("user"), dict) else {})
        login_u = str(user.get("login") or "")
        if not is_dependabot_patch_title(title, login_u):
            result.skipped.append(f"major-or-skip:{title[:60]}")
            continue
        repo_url = str(it.get("repository_url") or "")
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            continue
        owner, name = parts[-2], parts[-1]
        num = int(it["number"])
        try:
            client.put(
                f"/repos/{owner}/{name}/pulls/{num}/merge",
                allow_write=True,
                json={"merge_method": "squash", "commit_title": title},
            )
            result.merged.append(f"{owner}/{name}#{num}")
        except GitHubError as exc:
            result.errors.append(f"{owner}/{name}#{num}:{exc}")
    return result
