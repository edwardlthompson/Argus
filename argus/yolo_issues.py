"""Patterned GitHub Issue triage (deterministic — no product-bug invention)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import MatchedFix, RepoPlan

AUTO_CLOSE_LABELS = frozenset({"argus-auto", "argus:auto", "argus-auto-close"})
BOT_LOGINS = frozenset({
    "dependabot[bot]", "dependabot-preview[bot]", "github-actions[bot]", "renovate[bot]",
})
TITLE_MARKERS = (
    "argus-digest", "yolo-digest", "ci-digest", "steward-digest", "upgrade parent",
    "chore(argus)", "[argus]", "argus inbox", "argus-inbox",
)
NUDGE_MARKER = "<!-- argus:issue-stale-nudge -->"


def _labels(issue: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for lab in issue.get("labels") or []:
        name = str((lab.get("name") if isinstance(lab, dict) else lab) or "").strip().lower()
        if name:
            out.add(name)
    return out


def is_patterned_auto_close(issue: dict[str, Any]) -> bool:
    """True when Argus may close without inventing a product fix."""
    if issue.get("pull_request"):
        return False
    if _labels(issue) & AUTO_CLOSE_LABELS:
        return True
    title_l = str(issue.get("title") or "").lower()
    login = str((issue.get("user") or {}).get("login") or "").lower()
    if any(m in title_l for m in TITLE_MARKERS):
        return True
    if login in BOT_LOGINS and any(
        m in title_l for m in ("bump ", "update ", "upgrade ", "chore(", "security")
    ):
        return True
    return False


def triage_repo_issues(
    client: GitHubClient,
    plan: RepoPlan,
    matched: MatchedFix,
    *,
    stale_days: int = 90,
    max_close: int = 20,
) -> str:
    """Close patterned Issues; nudge other Issues idle ≥ stale_days."""
    owner, name = plan.repo.owner, plan.repo.name
    try:
        issues = client.get(
            f"/repos/{owner}/{name}/issues",
            params={"state": "open", "per_page": 50, "sort": "updated", "direction": "asc"},
        )
    except GitHubError as exc:
        return f"issue-triage-error:{plan.repo.full_name}:{exc}"
    if not isinstance(issues, list):
        return f"issue-triage-none:{plan.repo.full_name}"

    cutoff = datetime.now(UTC) - timedelta(days=max(1, stale_days))
    closed = nudged = skipped = 0
    for issue in issues:
        if issue.get("pull_request"):
            continue
        num = int(issue.get("number") or 0)
        if not num:
            continue
        if is_patterned_auto_close(issue):
            if closed >= max_close:
                skipped += 1
                continue
            try:
                client.patch(
                    f"/repos/{owner}/{name}/issues/{num}",
                    allow_write=True,
                    json={"state": "closed"},
                )
                client.post(
                    f"/repos/{owner}/{name}/issues/{num}/comments",
                    allow_write=True,
                    json={
                        "body": (
                            f"{NUDGE_MARKER}\nClosed by Argus continuous zero: patterned "
                            f"bot / `argus-auto` / digest Issue (`{matched.fix.id}`)."
                        )
                    },
                )
                closed += 1
            except GitHubError:
                skipped += 1
            continue
        raw_u = str(issue.get("updated_at") or "")
        try:
            when = datetime.fromisoformat(raw_u.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when > cutoff:
            continue
        try:
            comments = client.get(
                f"/repos/{owner}/{name}/issues/{num}/comments",
                params={"per_page": 30},
            )
            already = isinstance(comments, list) and any(
                NUDGE_MARKER in str(c.get("body") or "") for c in comments
            )
            if not already:
                client.post(
                    f"/repos/{owner}/{name}/issues/{num}/comments",
                    allow_write=True,
                    json={
                        "body": (
                            f"{NUDGE_MARKER}\nArgus: this Issue looks idle (≥{stale_days} days). "
                            "Please close, update, or label `needs-human`. "
                            "Argus will not auto-close human product Issues."
                        )
                    },
                )
                nudged += 1
        except GitHubError:
            skipped += 1
    return (
        f"issue-triage:{plan.repo.full_name}:closed={closed}:nudged={nudged}:skipped={skipped}"
    )
