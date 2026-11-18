"""Free-tier GitHub Actions outage detection (minutes / billing / no card).

Never treat “add a payment method” as the fix — Argus falls back to local PC
(`argus local-weekly`) and may skip remote CI for upgrade merges when Actions
cannot run.
"""

from __future__ import annotations

import os
from typing import Any

from argus.github_client import GitHubClient, GitHubError

# Annotation / summary fragments when GHA refuses to start the job.
BILLING_MARKERS = (
    "spending limit needs to be increased",
    "account payments have failed",
    "billing & plans",
    "actions minutes have been exceeded",
    "included minutes for this account have been exhausted",
    "free plan",
    "upgrade your account",
)

_UNAVAILABLE_CACHE: bool | None = None


def is_billing_text(text: str | None) -> bool:
    """True when text looks like an Actions billing / minutes block."""
    low = (text or "").lower()
    return any(m in low for m in BILLING_MARKERS)


def reset_actions_unavailable_cache() -> None:
    """Test helper — clear session cache."""
    global _UNAVAILABLE_CACHE
    _UNAVAILABLE_CACHE = None


def check_run_billing_blocked(
    client: GitHubClient,
    owner: str,
    name: str,
    check_run_id: int,
) -> bool:
    """True when this check-run failed because the job never started (billing)."""
    try:
        anns = client.get(
            f"/repos/{owner}/{name}/check-runs/{int(check_run_id)}/annotations",
        )
    except GitHubError:
        return False
    rows = anns if isinstance(anns, list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        blob = " ".join(
            str(row.get(k) or "")
            for k in ("message", "title", "raw_details")
        )
        if is_billing_text(blob):
            return True
    return False


def all_failed_checks_billing_only(
    client: GitHubClient,
    owner: str,
    name: str,
    failed_ids: list[int],
    *,
    max_probe: int = 12,
) -> bool:
    """True when every failed check-run is billing-blocked (none actually ran)."""
    ids = [int(i) for i in failed_ids if i][: max(1, max_probe)]
    if not ids:
        return False
    return all(check_run_billing_blocked(client, owner, name, cid) for cid in ids)


def _jobs_never_started(client: GitHubClient, owner: str, name: str, run_id: int) -> bool:
    try:
        data = client.get(f"/repos/{owner}/{name}/actions/runs/{int(run_id)}/jobs")
    except GitHubError:
        return False
    jobs = (data or {}).get("jobs") if isinstance(data, dict) else None
    if not jobs:
        return False
    for job in jobs:
        if not isinstance(job, dict):
            continue
        if str(job.get("conclusion") or "") != "failure":
            continue
        steps = job.get("steps")
        if isinstance(steps, list) and len(steps) == 0:
            return True
    return False


def _repo_recent_actions_dead(client: GitHubClient, owner: str, name: str) -> bool:
    try:
        data = client.get(
            f"/repos/{owner}/{name}/actions/runs",
            params={"per_page": 5, "status": "completed"},
        )
    except GitHubError:
        return False
    runs = (data or {}).get("workflow_runs") if isinstance(data, dict) else None
    for run in runs or []:
        if not isinstance(run, dict):
            continue
        if str(run.get("conclusion") or "") != "failure":
            continue
        rid = run.get("id")
        if rid is not None and _jobs_never_started(client, owner, name, int(rid)):
            return True
    return False


def actions_unavailable(
    client: GitHubClient,
    *,
    safety: dict[str, Any] | None = None,
    login: str | None = None,
) -> bool:
    """True when this account cannot run GitHub Actions (free minutes / no card).

    Honors ``ARGUS_ACTIONS_UNAVAILABLE=1|0`` and ``yolo.assume_actions_unavailable``.
    Otherwise probes ``{login}/argus-runner`` then ``{login}/Argus`` for zero-step
    failed jobs (classic billing/minutes refusal).
    """
    global _UNAVAILABLE_CACHE
    if _UNAVAILABLE_CACHE is not None:
        return _UNAVAILABLE_CACHE

    env = (os.environ.get("ARGUS_ACTIONS_UNAVAILABLE") or "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        _UNAVAILABLE_CACHE = True
        return True
    if env in ("0", "false", "no", "off"):
        _UNAVAILABLE_CACHE = False
        return False

    yolo = (safety or {}).get("yolo") or {}
    if bool(yolo.get("assume_actions_unavailable")):
        _UNAVAILABLE_CACHE = True
        return True

    me = login
    if not me:
        try:
            me = str((client.whoami() or {}).get("login") or "")
        except GitHubError:
            me = ""
    if me:
        for repo in (f"{me}/argus-runner", f"{me}/Argus"):
            owner, _, name = repo.partition("/")
            if name and _repo_recent_actions_dead(client, owner, name):
                _UNAVAILABLE_CACHE = True
                return True

    _UNAVAILABLE_CACHE = False
    return False


def summarize_billing(detail: dict[str, Any]) -> str:
    """One-line digest hint when CI is billing-blocked."""
    if not detail.get("billing"):
        return ""
    names = detail.get("failed") or []
    sample = ", ".join(str(n) for n in names[:4]) or "checks"
    return f"actions_billing:{sample}"
