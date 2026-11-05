"""End-to-end Argus run / report / fix pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from argus.agent_dispatch import (
    execute_dispatches,
    prepare_dispatches,
    summarize_dispatch,
)
from argus.apply import apply_auto_safe, summarize_apply
from argus.compose import write_artifacts
from argus.config_loader import load_fixes, load_profile, load_rubric, load_safety
from argus.discover import discover_portfolio
from argus.github_client import GitHubClient
from argus.inbox_issues import summarize_inbox, sync_inbox_issues
from argus.match import match_fixes
from argus.models import FixClass, RepoPlan
from argus.notify import send_notifications
from argus.score import score_repo
from argus.signals import collect_signals, fixture_bundle
from argus.state import StateStore


@dataclass
class RunSummary:
    mode: str
    repo_count: int
    human_tasks: int
    agent_repos: int
    artifacts: dict[str, str]
    details: dict[str, Any]


def build_plans_from_fixtures(
    fixtures: list[dict[str, Any]],
    *,
    profile: str = "generic",
    report_only: bool = False,
) -> list[RepoPlan]:
    """Test/helper path: build plans from canned fixture dicts (no network)."""
    from argus.models import RepoRecord, RepoStatus

    fixes = load_fixes()
    rubric = load_rubric()
    plans: list[RepoPlan] = []
    for item in fixtures:
        meta = item["repo"]
        status = RepoStatus(meta.get("status", "active"))
        repo = RepoRecord(
            full_name=meta["full_name"],
            owner=meta["full_name"].split("/")[0],
            name=meta["full_name"].split("/")[1],
            status=status,
            private=bool(meta.get("private")),
            archived=status == RepoStatus.ARCHIVED,
            fork=bool(meta.get("fork")),
            description=meta.get("description"),
            topics=list(meta.get("topics") or []),
            permissions={"push": not report_only and bool(meta.get("can_write", True))},
            html_url=meta.get("html_url", ""),
        )
        signals = fixture_bundle(item.get("signals") or {})
        score = score_repo(signals, rubric, status)
        matched = match_fixes(fixes, repo, signals, store=None, profile=profile)
        plan = RepoPlan(repo=repo, score=score, report_only=report_only)
        for m in matched:
            if m.fix.class_ == FixClass.HUMAN:
                plan.human_fixes.append(m)
            elif m.fix.class_ == FixClass.AGENT:
                plan.agent_fixes.append(m)
            else:
                plan.auto_fixes.append(m)
        plans.append(plan)
    return plans


def run_pipeline(
    *,
    dry_run: bool = True,
    target: str | None = None,
    public_only: bool = False,
    profile: str | None = None,
    notify: bool = True,
    report_url: str | None = None,
    token: str | None = None,
    include_archived: bool = False,
    run_agents: bool = False,
    attention_threshold: float | None = None,
) -> RunSummary:
    safety = load_safety()
    profile_name = profile or load_profile().get("name", "generic")
    rubric = load_rubric()
    fixes = load_fixes()
    mode = "report" if target else ("fix" if run_agents or not dry_run else "run")
    report_banner = "Read-only report — no changes were made." if target else None
    if not include_archived:
        # banner set after discovery if any skipped
        pass

    try:
        with GitHubClient(token=token, report_only=bool(target)) as client:
            store = StateStore()
            try:
                discovery = discover_portfolio(
                    client,
                    store,
                    target=target,
                    public_only=public_only,
                    include_archived=include_archived,
                )
                if discovery.skipped_archived and not report_banner:
                    n = len(discovery.skipped_archived)
                    report_banner = f"Skipped {n} archived repositories (use --include-archived to include)."

                plans: list[RepoPlan] = []
                for repo in discovery.repos:
                    signals = collect_signals(client, repo)
                    score = score_repo(signals, rubric, repo.status)
                    matched = match_fixes(fixes, repo, signals, store, profile=profile_name)
                    plan = RepoPlan(
                        repo=repo,
                        score=score,
                        report_only=discovery.report_only,
                    )
                    for m in matched:
                        if m.fix.class_ == FixClass.HUMAN:
                            plan.human_fixes.append(m)
                        elif m.fix.class_ == FixClass.AGENT:
                            plan.agent_fixes.append(m)
                        else:
                            plan.auto_fixes.append(m)
                    plans.append(plan)

                apply_result = apply_auto_safe(
                    client,
                    store,
                    plans,
                    dry_run=dry_run or discovery.report_only,
                    max_prs=int(safety["max_auto_prs_per_run"]),
                )

                threshold = (
                    float(attention_threshold)
                    if attention_threshold is not None
                    else float(safety.get("attention_threshold_for_agents", 60))
                )
                if run_agents:
                    threshold = 0.0
                max_sessions = int(safety["max_concurrent_agent_sessions"])
                if run_agents:
                    max_sessions = max(max_sessions, len([p for p in plans if p.agent_fixes]))

                dispatch = prepare_dispatches(
                    plans,
                    attention_threshold=threshold,
                    max_sessions=max_sessions if run_agents else int(safety["max_concurrent_agent_sessions"]),
                    max_prompt_chars=int(safety["max_agent_prompt_chars"]),
                )
                if run_agents and not discovery.report_only:
                    dispatch = execute_dispatches(client, store, plans, dispatch, dry_run=dry_run)

                md_path, html_path = write_artifacts(
                    plans,
                    max_prompt_chars=int(safety["max_agent_prompt_chars"]),
                    report_banner=report_banner,
                )
                inbox_result = None
                if not discovery.report_only:
                    inbox_result = sync_inbox_issues(client, store, plans, dry_run=dry_run)
                notify_result = None
                if notify and not discovery.report_only:
                    notify_result = send_notifications(plans, report_url=report_url)

                summary = RunSummary(
                    mode=mode,
                    repo_count=len(plans),
                    human_tasks=sum(len(p.human_fixes) for p in plans),
                    agent_repos=len(dispatch.queued),
                    artifacts={
                        "runbook": str(md_path),
                        "report": str(html_path),
                        "status": str(md_path.parent / "status.html"),
                        "inbox_json": str(md_path.parent / "inbox.json"),
                    },
                    details={
                        "new": discovery.new,
                        "removed": discovery.removed,
                        "skipped_archived": discovery.skipped_archived or [],
                        "apply": summarize_apply(apply_result),
                        "dispatch": summarize_dispatch(dispatch),
                        "inbox": None if inbox_result is None else summarize_inbox(inbox_result),
                        "notify": None
                        if notify_result is None
                        else {"sent": notify_result.sent, "skipped": notify_result.skipped},
                        "viewer": discovery.viewer,
                        "report_only": discovery.report_only,
                    },
                )
                store.add_history(
                    mode,
                    {
                        "repo_count": summary.repo_count,
                        "human_tasks": summary.human_tasks,
                        "dry_run": dry_run,
                    },
                )
                return summary
            finally:
                store.close()
    except Exception as exc:
        if notify:
            from argus.notify import send_error_notification

            send_error_notification(str(exc), report_url=report_url)
        raise
