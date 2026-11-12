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
    """No generation — open a brief-only PR that documents the design ask."""
    state = "missing"
    try:
        from argus.signals.hygiene import _brand_icon as probe

        probe_out = probe(client, plan.repo)
        state = str(probe_out.get("brand_icon_state") or "missing")
    except Exception:  # noqa: BLE001
        pass
    body = (
        f"# Brand icon brief — `{plan.repo.full_name}`\n\n"
        f"Argus state: **{state}** (only `owned` passes).\n\n"
        "## Design brief\n\n"
        "- Provide a **square** app mark (PNG ≥512px) at `branding/assets/app-icon-512.png` "
        "(or another canonical path in `config/profile_icons.yaml`).\n"
        "- Do **not** use social-preview, splash, favicon, wordmark, lockup, or stub SVG.\n"
        "- Do **not** copy the parent template icon unchanged (that is `inherited`).\n"
        "- Argus will not generate or invent artwork.\n"
    )
    path = "docs/BRAND_ICON_BRIEF.md"
    return _content_pr(
        client,
        plan,
        matched,
        path,
        body,
        "chore(argus): brand icon design brief (no generated asset)",
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


def _issue_patterned(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    from argus.yolo_issues import triage_repo_issues

    return triage_repo_issues(client, plan, matched, stale_days=90)


def _stale_issues(client: GitHubClient, plan: RepoPlan, matched: MatchedFix) -> str:
    from argus.yolo_issues import triage_repo_issues

    return triage_repo_issues(client, plan, matched, stale_days=90)


YOLO_HANDLERS = {
    "SEC-CODEQL": _sec_codeql,
    "SEC-OPEN-DEPENDABOT-ALERTS": _dependabot_security_updates,
    "BRAND-ICON-MISSING": _brand_icon,
    "LINEAGE-RECOMMEND-UPGRADE": _lineage_version,
    "AGENT-WHAT-NOT": _what_not,
    "AGENT-MEMORY-LAYOUT": _memory_layout,
    "ISSUE-PATTERNED-AUTO": _issue_patterned,
    "AGENT-STALE-ISSUES": _stale_issues,
}

# Deterministic agent-class handlers (always eligible when handlers run).
YOLO_AGENT_HANDLERS = frozenset({
    "AGENT-WHAT-NOT",
    "AGENT-MEMORY-LAYOUT",
    "PR-STALE",
    "SEC-CODEQL",
    "LINEAGE-RECOMMEND-UPGRADE",
    "ISSUE-PATTERNED-AUTO",
    "AGENT-STALE-ISSUES",
})

# Catalogue may still say human; continuous zero applies these via API.
YOLO_API_SAFE_HANDLERS = frozenset({
    "SEC-CODEQL",
    "SEC-OPEN-DEPENDABOT-ALERTS",
    "LINEAGE-RECOMMEND-UPGRADE",
})

# Never auto-clear — judgment / artwork only.
YOLO_JUDGMENT_ONLY = frozenset({
    "BRAND-ICON-MISSING",
    "HUMAN-PARK-INACTIVE",
    "HUMAN-ARCHIVE-JUDGMENT",
})


def is_yolo_deterministic_agent(matched: MatchedFix) -> bool:
    from argus.models import FixClass

    return matched.fix.class_ == FixClass.AGENT and (
        matched.fix.id in YOLO_AGENT_HANDLERS or matched.fix.id in YOLO_HANDLERS
    )


def apply_yolo_extras(
    client: GitHubClient,
    store: StateStore,
    plans: list[RepoPlan],
    *,
    dry_run: bool,
    max_actions: int,
    yolo_cfg: dict[str, Any] | None = None,
) -> YoloResult:
    """Run deterministic handlers (continuous zero).

    When ``apply_api_handlers`` is true (default under YOLO / continuous zero),
    API-safe catalogue rows run even if class is still human. Judgment-only
    ids (brand art, park/archive) stay digest-only.
    """
    cfg = yolo_cfg or {}
    apply_api = bool(cfg.get("apply_api_handlers", False))
    resolve_ci = bool(cfg.get("resolve_ci_when_actions_unavailable", False))
    actions_down = False
    if resolve_ci:
        try:
            from argus.actions_billing import actions_unavailable
            from argus.config_loader import load_safety

            actions_down = bool(actions_unavailable(client, safety=load_safety()))
        except Exception:  # noqa: BLE001
            actions_down = bool(
                __import__("os").environ.get("ARGUS_ACTIONS_UNAVAILABLE", "").strip()
                in ("1", "true", "yes", "on")
            )
    idle = int(cfg.get("stale_pr_idle_days") or cfg.get("close_stale_bot_prs_days") or 30)
    result = YoloResult()
    if client.report_only or dry_run:
        for plan in plans:
            for m in list(plan.agent_fixes) + list(plan.human_fixes):
                if (
                    is_yolo_deterministic_agent(m)
                    or m.fix.id == "PR-STALE"
                    or (apply_api and m.fix.id in YOLO_API_SAFE_HANDLERS)
                ):
                    result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:dry_run")
        return result
    n = 0

    def _run_handler(plan: RepoPlan, m: MatchedFix, handler) -> None:
        nonlocal n
        if n >= max_actions:
            result.skipped.append(f"{plan.repo.full_name}:{m.fix.id}:max_actions")
            return
        key = f"{plan.repo.full_name}:{m.fix.id}"
        try:
            if m.fix.id == "PR-STALE":
                url = _pr_stale(client, plan, m, idle_days=idle)
            else:
                url = handler(client, plan, m)
            result.applied.append(key)
            result.opened_prs.append(url)
            store.record_resolution(
                plan.repo.full_name,
                m.fix.id,
                ttl_days=m.fix.resolution_ttl_days or 30,
                source="yolo",
            )
            n += 1
        except GitHubError as exc:
            result.errors.append(f"{key}:{exc}")

    for plan in plans:
        if not plan.repo.can_write:
            continue
        # Agent + human bags: continuous zero treats deterministic ids uniformly.
        bag = list(plan.human_fixes) + list(plan.agent_fixes)
        for m in bag:
            fid = m.fix.id
            if fid == "CI-LATEST-FAILED":
                result.digest_notes.append(
                    f"- `{plan.repo.full_name}` · `{fid}` — {m.fix.title}"
                )
                if resolve_ci and actions_down:
                    store.record_resolution(
                        plan.repo.full_name,
                        fid,
                        ttl_days=7,
                        source="actions_unavailable",
                    )
                    result.applied.append(f"{plan.repo.full_name}:{fid}")
                    n += 1
                else:
                    result.skipped.append(f"{plan.repo.full_name}:{fid}:needs_triage")
                continue
            if fid in YOLO_JUDGMENT_ONLY:
                result.digest_notes.append(
                    f"- `{plan.repo.full_name}` · `{fid}` — {m.fix.title} (judgment)"
                )
                result.skipped.append(f"{plan.repo.full_name}:{fid}:judgment")
                continue
            if fid == "PR-STALE" or fid in YOLO_AGENT_HANDLERS or (
                apply_api and fid in YOLO_API_SAFE_HANDLERS
            ):
                handler = None if fid == "PR-STALE" else YOLO_HANDLERS.get(fid)
                if fid != "PR-STALE" and not handler:
                    continue
                _run_handler(plan, m, handler)
                continue
            if fid in YOLO_HANDLERS and not apply_api:
                result.digest_notes.append(
                    f"- `{plan.repo.full_name}` · `{fid}` — {m.fix.title} (human; not YOLO)"
                )
                result.skipped.append(f"{plan.repo.full_name}:{fid}:human_class")
    return result


def pr_ci_detail(
    client: GitHubClient,
    owner: str,
    name: str,
    sha: str | None,
    *,
    probe_billing: bool = False,
) -> dict[str, Any]:
    """Return {state, failed, failed_ids, pending, billing} for commit check-runs."""
    empty = {
        "state": "unknown",
        "failed": [],
        "failed_ids": [],
        "pending": False,
        "billing": False,
    }
    if not sha:
        return empty
    try:
        client.get(f"/repos/{owner}/{name}/commits/{sha}/status")
    except GitHubError:
        pass
    try:
        runs = client.get(
            f"/repos/{owner}/{name}/commits/{sha}/check-runs",
            params={"per_page": 100},
        )
        items = (runs or {}).get("check_runs") if isinstance(runs, dict) else None
        if not items:
            return {
                "state": "green",
                "failed": [],
                "failed_ids": [],
                "pending": False,
                "billing": False,
            }
        pending = any(str(c.get("status") or "") != "completed" for c in items)
        failed_rows = [
            c
            for c in items
            if str(c.get("status") or "") == "completed"
            and str(c.get("conclusion") or "")
            in ("failure", "timed_out", "cancelled", "action_required")
        ]
        failed = [str(c.get("name") or "?") for c in failed_rows]
        failed_ids = [int(c["id"]) for c in failed_rows if c.get("id") is not None]
        billing = False
        if probe_billing and failed_ids and not pending:
            from argus.actions_billing import all_failed_checks_billing_only

            billing = all_failed_checks_billing_only(
                client, owner, name, failed_ids
            )
        if pending:
            return {
                "state": "pending",
                "failed": failed,
                "failed_ids": failed_ids,
                "pending": True,
                "billing": False,
            }
        if failed:
            return {
                "state": "failed",
                "failed": failed,
                "failed_ids": failed_ids,
                "pending": False,
                "billing": billing,
            }
        return {
            "state": "green",
            "failed": [],
            "failed_ids": [],
            "pending": False,
            "billing": False,
        }
    except GitHubError:
        return empty


def _pr_ci_status(client: GitHubClient, owner: str, name: str, sha: str | None) -> str:
    """Return green | pending | failed | unknown (no sha)."""
    return str(pr_ci_detail(client, owner, name, sha).get("state") or "unknown")


def _pr_ci_green(client: GitHubClient, owner: str, name: str, sha: str | None) -> bool:
    return _pr_ci_status(client, owner, name, sha) == "green"


def _squash_merge_search(
    client: GitHubClient,
    *,
    query: str,
    max_merges: int,
    login: str | None,
    safety: dict[str, Any],
    head_prefixes: tuple[str, ...] | None = None,
    require_armed: bool = True,
    soft_allowlist: bool = False,
) -> YoloResult:
    from argus.yolo_arm import is_yolo_armed
    from argus.yolo_checks import evaluate_pre_merge
    from argus.yolo_upgrade_fix import soft_merge_ok

    result = YoloResult()
    if client.report_only:
        result.skipped.append("report_only")
        return result
    if require_armed and not is_yolo_armed(safety):
        result.skipped.append("yolo_not_armed")
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
            params={"q": query.replace("{me}", me), "per_page": min(100, max(1, max_merges))},
        )
    except GitHubError as exc:
        result.errors.append(str(exc))
        return result
    items = data.get("items") if isinstance(data, dict) else []
    skip_profile = bool((safety.get("yolo") or {}).get("skip_profile", True))
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
        sha = None
        head_ref = ""
        try:
            pr = client.get(f"/repos/{owner}/{name}/pulls/{num}")
            sha = str(((pr or {}).get("head") or {}).get("sha") or "") or None
            head_ref = str(((pr or {}).get("head") or {}).get("ref") or "")
        except GitHubError:
            pass
        if head_prefixes and not any(head_ref.startswith(p) for p in head_prefixes):
            result.skipped.append(f"{owner}/{name}#{num}:head={head_ref or '?'}")
            continue
        is_profile = owner.lower() == name.lower()
        yolo_cfg = safety.get("yolo") or {}
        allow_billing = bool(yolo_cfg.get("merge_when_actions_billing", True))
        skip_ci_unavailable = bool(
            yolo_cfg.get("skip_ci_when_actions_unavailable", True)
        )
        from argus.actions_billing import actions_unavailable

        unavailable = skip_ci_unavailable and actions_unavailable(
            client, safety=safety, login=me
        )
        detail = pr_ci_detail(
            client,
            owner,
            name,
            sha,
            probe_billing=bool(
                soft_allowlist and allow_billing and not unavailable
            ),
        )
        ci_state = str(detail.get("state") or "unknown")
        failed_names = list(detail.get("failed") or [])
        ci_ok = ci_state == "green"
        if unavailable and not ci_ok:
            # Free-tier / no-card: never block upgrades on paid Actions.
            ci_ok = True
            ci_state = "actions_unavailable"
        elif not ci_ok and soft_allowlist and ci_state == "failed" and soft_merge_ok(failed_names):
            ci_ok = True
            ci_state = "soft_allowlist"
        elif (
            not ci_ok
            and soft_allowlist
            and allow_billing
            and ci_state == "failed"
            and bool(detail.get("billing"))
        ):
            # Jobs never started (billing/minutes) — local/PC fallback path.
            ci_ok = True
            ci_state = "actions_billing"
        ok, failed = evaluate_pre_merge(
            safety=safety,
            title=title,
            ci_green=ci_ok,
            is_profile_repo=is_profile,
            skip_profile=skip_profile,
            require_armed=require_armed,
        )
        if not ok:
            tag = ",".join(failed)
            if "ci_green" in failed:
                extra = ",".join(failed_names[:5]) if failed_names else ci_state
                tag = f"{tag}:{ci_state}:{extra}"
            result.skipped.append(f"{owner}/{name}#{num}:checks={tag}")
            continue
        try:
            client.put(
                f"/repos/{owner}/{name}/pulls/{num}/merge",
                allow_write=True,
                json={"merge_method": "squash", "commit_title": title},
            )
            result.merged.append(f"{owner}/{name}#{num}")
            try:
                from argus.action_ledger import append_action

                suffix = {
                    "soft_allowlist": " (soft)",
                    "actions_billing": " (actions_billing)",
                    "actions_unavailable": " (actions_unavailable)",
                }.get(ci_state, "")
                append_action(
                    actor="yolo",
                    repo=f"{owner}/{name}",
                    action="squash_merge",
                    detail=f"{title}{suffix}",
                    pr_url=str(it.get("html_url") or ""),
                    sha_after=sha,
                )
            except Exception:  # noqa: BLE001
                pass
        except GitHubError as exc:
            result.errors.append(f"{owner}/{name}#{num}:{exc}")
    return result


def merge_argus_prs(
    client: GitHubClient,
    *,
    max_merges: int,
    login: str | None = None,
    safety: dict[str, Any] | None = None,
) -> YoloResult:
    """Squash-merge open PRs titled chore(argus) for the authenticated user."""
    from argus.config_loader import load_safety

    safety = safety or load_safety()
    return _squash_merge_search(
        client,
        query='user:{me} is:pr is:open "chore(argus)" in:title',
        max_merges=max_merges,
        login=login,
        safety=safety,
        head_prefixes=("chore/argus",),
        require_armed=True,
    )


def merge_upgrade_prs(
    client: GitHubClient,
    *,
    max_merges: int,
    login: str | None = None,
    safety: dict[str, Any] | None = None,
    require_armed: bool = True,
    soft_allowlist: bool | None = None,
) -> YoloResult:
    """Squash-merge parent-upgrade PRs (chore/argus-upgrade-*)."""
    from argus.config_loader import load_safety

    safety = safety or load_safety()
    yolo_cfg = safety.get("yolo") or {}
    if soft_allowlist is None:
        soft_allowlist = bool(yolo_cfg.get("soft_merge_upgrade_noise", False))
    return _squash_merge_search(
        client,
        query='user:{me} is:pr is:open "upgrade parent rules" in:title',
        max_merges=max_merges,
        login=login,
        safety=safety,
        head_prefixes=("chore/argus-upgrade-",),
        require_armed=require_armed,
        soft_allowlist=bool(soft_allowlist),
    )


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
