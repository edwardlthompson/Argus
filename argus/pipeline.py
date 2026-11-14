"""End-to-end Argus run / report / fix pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from argus.action_ledger import record_actions
from argus.agent_dispatch import (
    execute_dispatches,
    prepare_dispatches,
    summarize_dispatch,
)
from argus.agent_ops import prompt_budget_report
from argus.apply import apply_auto_safe, summarize_apply
from argus.apply_history import record_apply_history
from argus.compose import write_artifacts
from argus.config_loader import load_fixes, load_profile, load_rubric, load_safety
from argus.dependabot_policy import (
    allowed_levels as dependabot_levels,
)
from argus.dependabot_policy import (
    merge_enabled as dependabot_merge_enabled,
)
from argus.discover import discover_portfolio
from argus.github_client import GitHubClient
from argus.health import (
    clear_auto_fixes_for_repos,
    compare_snapshots,
    project_plans_after_apply,
    snapshot_plans,
    write_health_artifacts,
)
from argus.inbox_issues import summarize_inbox, sync_inbox_issues
from argus.inbox_project import summarize_project, sync_inbox_project
from argus.match import match_fixes
from argus.models import FixClass, RepoPlan
from argus.notify import send_notifications
from argus.profile_apply import ProfileApplyResult, sync_profile_readme
from argus.quiet_log import emit_run_line
from argus.rate_limit import CoreQuota
from argus.score import score_repo
from argus.signals import collect_signals, fixture_bundle
from argus.state import StateStore
from argus.triage import fleet_rollup, summarize_triage
from argus.yolo import (
    YoloResult,
    apply_yolo_extras,
    merge_argus_prs,
    merge_dependabot_prs,
    merge_upgrade_prs,
)
from argus.yolo_arm import is_yolo_armed
from argus.yolo_digest import collect_judgment_items, sync_report_files, upsert_yolo_digest


def _quota_from_safety(safety: dict[str, Any]) -> CoreQuota:
    api = safety.get("github_api") or {}
    return CoreQuota(
        limit=int(api.get("core_limit_hint") or 5000),
        reserve=int(api.get("reserve") or 250),
        min_interval=float(api.get("min_interval_ms") or 80) / 1000.0,
        max_interval=float(api.get("max_interval_ms") or 2000) / 1000.0,
        calls_per_repo_estimate=int(api.get("calls_per_repo_estimate") or 50),
        max_wait_seconds=float(api.get("max_wait_seconds") or 3700),
    )


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


def _score_batch(
    client: GitHubClient,
    repos: list[Any],
    *,
    fixes: list[Any],
    rubric: dict[str, Any],
    store: StateStore,
    profile_name: str,
    report_only: bool,
    batch_size: int,
    per_repo: int,
    quota: CoreQuota,
) -> list[RepoPlan]:
    plans: list[RepoPlan] = []
    for offset in range(0, len(repos), batch_size):
        batch = repos[offset : offset + batch_size]
        client.ensure_budget(needed=len(batch) * per_repo + quota.reserve)
        for repo in batch:
            signals = collect_signals(client, repo)
            score = score_repo(signals, rubric, repo.status)
            matched = match_fixes(fixes, repo, signals, store, profile=profile_name)
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


def _yolo_eligible_left(plans: list[RepoPlan], *, apply_api: bool = False) -> bool:
    from argus.yolo import (
        YOLO_API_SAFE_HANDLERS,
        YOLO_HANDLERS,
        is_yolo_deterministic_agent,
    )

    for plan in plans:
        for m in plan.auto_fixes:
            if m.fix.class_ == FixClass.AUTO_SAFE:
                return True
        for m in list(plan.agent_fixes) + list(plan.human_fixes):
            if is_yolo_deterministic_agent(m):
                return True
            if m.fix.id in YOLO_HANDLERS or m.fix.id == "PR-STALE":
                return True
            if apply_api and m.fix.id in YOLO_API_SAFE_HANDLERS:
                return True
    return False


def _maybe_auto_rules_sync(safety: dict[str, Any], *, yolo_on: bool, dry_run: bool) -> dict[str, Any] | None:
    """Refresh rules lock when continuous-zero asks for auto_rules_sync."""
    if dry_run:
        return None
    normal_cfg = safety.get("normal") or {}
    yolo_cfg = safety.get("yolo") or {}
    want = bool(
        (yolo_on and yolo_cfg.get("auto_rules_sync", True))
        or ((not yolo_on) and normal_cfg.get("auto_rules_sync", True))
    )
    if not want:
        return None
    try:
        from argus.rules_sync import rules_stale, sync_lock

        if not rules_stale():
            return {"synced": False, "reason": "fresh"}
        return {"synced": True, "lock": sync_lock()}
    except Exception as exc:  # noqa: BLE001
        return {"synced": False, "error": str(exc)}


def _handlers_cfg(safety: dict[str, Any], *, yolo_on: bool) -> dict[str, Any]:
    """Merge YOLO + normal continuous-zero flags for apply_yolo_extras."""
    yolo_cfg = dict(safety.get("yolo") or {})
    normal_cfg = safety.get("normal") or {}
    if yolo_on:
        return yolo_cfg
    # Vanilla --apply: enable handlers + API-safe path from continuous zero.
    out = dict(yolo_cfg)
    if normal_cfg.get("yolo_handlers", True) or normal_cfg.get("continuous_zero", True):
        out["apply_api_handlers"] = True
        out.setdefault(
            "resolve_ci_when_actions_unavailable",
            yolo_cfg.get("resolve_ci_when_actions_unavailable", True),
        )
    return out


def run_pipeline(
    *,
    dry_run: bool | None = True,
    target: str | None = None,
    public_only: bool = False,
    profile: str | None = None,
    notify: bool = True,
    report_url: str | None = None,
    token: str | None = None,
    include_archived: bool = False,
    run_agents: bool = False,
    attention_threshold: float | None = None,
    skip_profile: bool | None = None,
) -> RunSummary:
    safety = load_safety()
    profile_name = profile or load_profile().get("name", "generic")
    rubric = load_rubric()
    fixes = load_fixes()
    yolo_cfg = safety.get("yolo") or {}
    normal_cfg = safety.get("normal") or {}
    yolo_on = is_yolo_armed(safety)

    # YOLO implies apply unless caller passed an explicit dry_run=True.
    # CLI uses dry_run=None when neither --dry-run nor --apply was set.
    if dry_run is None:
        dry_run = not yolo_on
    # CLI: None = defaults; True = --skip-profile; False = --with-profile.
    cli_skip_profile = skip_profile
    if skip_profile is None:
        skip_profile = bool(yolo_on and yolo_cfg.get("skip_profile", True))
    # Overview sync (stats/icons/membership) is separate from skip_profile mutations.
    plane_cfg = yolo_cfg if yolo_on else normal_cfg
    if cli_skip_profile is True:
        sync_profile = False
    elif cli_skip_profile is False:
        sync_profile = True
    else:
        sync_profile = bool(plane_cfg.get("sync_profile", True))

    mode = "report" if target else ("fix" if run_agents or not dry_run else "run")
    report_banner = "Read-only report — no changes were made." if target else None
    rules_sync_meta = _maybe_auto_rules_sync(safety, yolo_on=yolo_on, dry_run=bool(dry_run))

    try:
        quota = _quota_from_safety(safety)
        api_cfg = safety.get("github_api") or {}
        batch_size = max(1, int(api_cfg.get("max_repos_per_batch") or 6))
        per_repo = max(1, int(api_cfg.get("calls_per_repo_estimate") or 50))
        with GitHubClient(token=token, report_only=bool(target), quota=quota) as client:
            store = StateStore()
            try:
                client.ensure_budget(needed=max(quota.reserve, 50))
                discovery = discover_portfolio(
                    client,
                    store,
                    target=target,
                    public_only=public_only,
                    include_archived=include_archived,
                )
                if discovery.skipped_archived and not report_banner:
                    n = len(discovery.skipped_archived)
                    report_banner = (
                        f"Skipped {n} archived repositories "
                        "(use --include-archived to include)."
                    )

                plans = _score_batch(
                    client,
                    list(discovery.repos),
                    fixes=fixes,
                    rubric=rubric,
                    store=store,
                    profile_name=profile_name,
                    report_only=discovery.report_only,
                    batch_size=batch_size,
                    per_repo=per_repo,
                    quota=quota,
                )

                profile_login = ""
                try:
                    profile_login = str((client.whoami() or {}).get("login") or "")
                except Exception:  # noqa: BLE001
                    profile_login = ""
                profile_repo = f"{profile_login}/{profile_login}" if profile_login else ""
                if skip_profile and profile_repo:
                    clear_auto_fixes_for_repos(plans, {profile_repo})

                before_health = snapshot_plans(plans)

                def _apply_once(current: list[RepoPlan]) -> tuple[dict[str, Any], Any, Any, Any]:
                    max_prs = int(safety["max_auto_prs_per_run"])
                    apply_budget = max(
                        1, ((client.quota.remaining or per_repo) - quota.reserve) // 8
                    )
                    if not dry_run and not discovery.report_only:
                        max_prs = min(max_prs, apply_budget)
                        client.ensure_budget(needed=max_prs * 8 + quota.reserve)

                    apply_result = apply_auto_safe(
                        client,
                        store,
                        current,
                        dry_run=dry_run or discovery.report_only,
                        max_prs=max_prs,
                        max_prs_per_owner=int(safety.get("max_auto_prs_per_owner") or 0) or None,
                    )
                    apply_summary = summarize_apply(apply_result)
                    yolo_extra = None
                    yolo_merge = None
                    yolo_dep = None
                    # Vanilla (normal + explicit --apply): mechanical upgrade heal/fix only.
                    ncfg = safety.get("normal") or {}
                    if (
                        not yolo_on
                        and not dry_run
                        and not discovery.report_only
                        and (
                            ncfg.get("fix_upgrade_prs", True)
                            or ncfg.get("heal_upgrade_prs", True)
                        )
                    ):
                        try:
                            max_up = int(yolo_cfg.get("max_auto_merges_per_day") or 20)
                            if ncfg.get("fix_upgrade_prs", True):
                                from argus.yolo_upgrade_fix import fix_open_upgrade_prs

                                vf = fix_open_upgrade_prs(
                                    client,
                                    login=profile_login or None,
                                    max_repos=max_up,
                                )
                                apply_summary = {
                                    **apply_summary,
                                    "vanilla_fix_upgrades": vf,
                                }
                            elif ncfg.get("heal_upgrade_prs", True):
                                from argus.yolo_upgrade_heal import heal_open_upgrade_prs

                                vh = heal_open_upgrade_prs(
                                    client,
                                    login=profile_login or None,
                                    max_repos=max_up,
                                )
                                apply_summary = {
                                    **apply_summary,
                                    "vanilla_heal_upgrades": vh,
                                }
                        except Exception as exc:  # noqa: BLE001
                            apply_summary = {
                                **apply_summary,
                                "vanilla_upgrade_error": str(exc),
                            }
                    if (
                        not yolo_on
                        and not dry_run
                        and not discovery.report_only
                        and dependabot_merge_enabled(safety, yolo=False)
                    ):
                        rem = int(yolo_cfg.get("max_auto_merges_per_day") or 20)
                        yolo_dep = merge_dependabot_prs(
                            client,
                            max_merges=rem,
                            login=profile_login or None,
                            safety=safety,
                            require_armed=False,
                            allowed_levels=dependabot_levels(safety, yolo=False),
                        )
                    run_handlers = (
                        not discovery.report_only
                        and (
                            yolo_on
                            or (
                                not dry_run
                                and (
                                    ncfg.get("yolo_handlers", True)
                                    or ncfg.get("continuous_zero", True)
                                )
                            )
                        )
                    )
                    if run_handlers:
                        handlers_cfg = _handlers_cfg(safety, yolo_on=yolo_on)
                        yolo_extra = apply_yolo_extras(
                            client,
                            store,
                            current,
                            dry_run=dry_run,
                            max_actions=int(yolo_cfg.get("max_yolo_actions_per_run") or 40),
                            yolo_cfg=handlers_cfg,
                        )
                        apply_summary = {
                            **apply_summary,
                            "applied": list(apply_summary.get("applied") or [])
                            + list(yolo_extra.applied),
                            "opened_prs": list(apply_summary.get("opened_prs") or [])
                            + list(yolo_extra.opened_prs),
                            "errors": list(apply_summary.get("errors") or [])
                            + list(yolo_extra.errors),
                            "skipped": list(apply_summary.get("skipped") or [])
                            + list(yolo_extra.skipped),
                            "continuous_zero": True,
                        }
                        drop = set(yolo_extra.applied)
                        for plan in current:
                            plan.human_fixes = [
                                m
                                for m in plan.human_fixes
                                if f"{plan.repo.full_name}:{m.fix.id}" not in drop
                            ]
                            plan.agent_fixes = [
                                m
                                for m in plan.agent_fixes
                                if f"{plan.repo.full_name}:{m.fix.id}" not in drop
                            ]
                    if yolo_on and not discovery.report_only:
                        if (
                            not dry_run
                            and yolo_cfg.get("auto_merge_auto_safe", True)
                        ):
                            yolo_merge = merge_argus_prs(
                                client,
                                max_merges=int(yolo_cfg.get("max_auto_merges_per_day") or 20),
                                login=profile_login or None,
                            )
                        if (
                            not dry_run
                            and yolo_cfg.get("auto_merge_upgrade_prs", True)
                            and yolo_cfg.get("clear_upgrade_blockers", True)
                        ):
                            from argus.yolo_clear_blockers import clear_open_upgrade_blockers

                            rem_up = int(yolo_cfg.get("max_auto_merges_per_day") or 20)
                            if yolo_merge:
                                rem_up = max(0, rem_up - len(yolo_merge.merged))
                            cleared = clear_open_upgrade_blockers(
                                client,
                                login=profile_login or None,
                                max_merges=rem_up,
                                loops=int(yolo_cfg.get("clear_upgrade_loops") or 8),
                                sleep_s=int(yolo_cfg.get("clear_upgrade_sleep_s") or 90),
                                soft_allowlist=bool(
                                    yolo_cfg.get("soft_merge_upgrade_noise", True)
                                ),
                                require_armed=True,
                                also_dependabot_patch=dependabot_merge_enabled(
                                    safety, yolo=True
                                ),
                            )
                            up = YoloResult()
                            up.merged.extend(cleared.get("merged") or [])
                            up.skipped.extend(cleared.get("leftovers") or [])
                            for round_row in cleared.get("rounds") or []:
                                up.errors.extend(round_row.get("errors") or [])
                            if yolo_merge is None:
                                yolo_merge = up
                            else:
                                yolo_merge.merged.extend(up.merged)
                                yolo_merge.skipped.extend(up.skipped)
                                yolo_merge.errors.extend(up.errors)
                            yolo_dep = YoloResult()
                            yolo_dep.merged.extend(cleared.get("dep_merged") or [])
                        elif (
                            not dry_run
                            and yolo_cfg.get("auto_merge_upgrade_prs", True)
                        ):
                            try:
                                max_up = int(yolo_cfg.get("max_auto_merges_per_day") or 20)
                                if yolo_cfg.get("fix_upgrade_prs", True):
                                    from argus.yolo_upgrade_fix import fix_open_upgrade_prs

                                    fix_open_upgrade_prs(
                                        client,
                                        login=profile_login or None,
                                        max_repos=max_up,
                                    )
                                elif yolo_cfg.get("heal_upgrade_prs", True):
                                    from argus.yolo_upgrade_heal import heal_open_upgrade_prs

                                    heal_open_upgrade_prs(
                                        client,
                                        login=profile_login or None,
                                        max_repos=max_up,
                                    )
                            except Exception:  # noqa: BLE001
                                pass
                            rem_up = int(yolo_cfg.get("max_auto_merges_per_day") or 20)
                            if yolo_merge:
                                rem_up = max(0, rem_up - len(yolo_merge.merged))
                            up = merge_upgrade_prs(
                                client,
                                max_merges=rem_up,
                                login=profile_login or None,
                                soft_allowlist=bool(
                                    yolo_cfg.get("soft_merge_upgrade_noise", False)
                                ),
                            )
                            if yolo_merge is None:
                                yolo_merge = up
                            else:
                                yolo_merge.merged.extend(up.merged)
                                yolo_merge.skipped.extend(up.skipped)
                                yolo_merge.errors.extend(up.errors)
                            if dependabot_merge_enabled(safety, yolo=True):
                                rem = int(yolo_cfg.get("max_auto_merges_per_day") or 20)
                                if yolo_merge:
                                    rem = max(0, rem - len(yolo_merge.merged))
                                yolo_dep = merge_dependabot_prs(
                                    client,
                                    max_merges=rem,
                                    login=profile_login or None,
                                    safety=safety,
                                    require_armed=True,
                                    allowed_levels=dependabot_levels(safety, yolo=True),
                                )
                        elif (
                            not dry_run
                            and dependabot_merge_enabled(safety, yolo=True)
                        ):
                            rem = int(yolo_cfg.get("max_auto_merges_per_day") or 20)
                            if yolo_merge:
                                rem = max(0, rem - len(yolo_merge.merged))
                            yolo_dep = merge_dependabot_prs(
                                client,
                                max_merges=rem,
                                login=profile_login or None,
                                safety=safety,
                                require_armed=True,
                                allowed_levels=dependabot_levels(safety, yolo=True),
                            )
                    project_plans_after_apply(
                        current, apply_summary, dry_run=dry_run or discovery.report_only
                    )
                    return apply_summary, yolo_extra, yolo_merge, yolo_dep

                apply_summary, yolo_extra, yolo_merge, yolo_dep = _apply_once(plans)
                if rules_sync_meta:
                    apply_summary = {**apply_summary, "rules_sync": rules_sync_meta}

                second_pass = False
                want_second = bool(
                    (
                        yolo_on
                        and yolo_cfg.get("second_pass_if_budget", True)
                        and (
                            yolo_cfg.get("continuous_zero", True)
                            or yolo_cfg.get("second_pass_if_budget", True)
                        )
                    )
                    or (
                        (not yolo_on)
                        and not dry_run
                        and (
                            normal_cfg.get("second_pass", True)
                            or normal_cfg.get("continuous_zero", True)
                        )
                    )
                )
                apply_api = bool(
                    (yolo_on and yolo_cfg.get("apply_api_handlers", True))
                    or (not yolo_on and normal_cfg.get("yolo_handlers", True))
                )
                if (
                    want_second
                    and not dry_run
                    and not discovery.report_only
                    and _yolo_eligible_left(plans, apply_api=apply_api)
                ):
                    remaining = int(client.quota.remaining or 0)
                    need = batch_size * per_repo + quota.reserve
                    if remaining > need:
                        second_pass = True
                        plans = _score_batch(
                            client,
                            list(discovery.repos),
                            fixes=fixes,
                            rubric=rubric,
                            store=store,
                            profile_name=profile_name,
                            report_only=discovery.report_only,
                            batch_size=batch_size,
                            per_repo=per_repo,
                            quota=quota,
                        )
                        if skip_profile and profile_repo:
                            clear_auto_fixes_for_repos(plans, {profile_repo})
                        s2, xe2, xm2, xd2 = _apply_once(plans)
                        apply_summary = {
                            **apply_summary,
                            "applied": list(apply_summary.get("applied") or [])
                            + list(s2.get("applied") or []),
                            "opened_prs": list(apply_summary.get("opened_prs") or [])
                            + list(s2.get("opened_prs") or []),
                            "errors": list(apply_summary.get("errors") or [])
                            + list(s2.get("errors") or []),
                            "skipped": list(apply_summary.get("skipped") or [])
                            + list(s2.get("skipped") or []),
                            "second_pass": True,
                        }
                        if xe2:
                            yolo_extra = xe2 if yolo_extra is None else yolo_extra
                            if yolo_extra is not xe2:
                                yolo_extra.applied.extend(xe2.applied)
                                yolo_extra.errors.extend(xe2.errors)
                                yolo_extra.digest_notes.extend(xe2.digest_notes)
                        if xm2:
                            if yolo_merge is None:
                                yolo_merge = xm2
                            else:
                                yolo_merge.merged.extend(xm2.merged)
                                yolo_merge.errors.extend(xm2.errors)
                        if xd2:
                            if yolo_dep is None:
                                yolo_dep = xd2
                            else:
                                yolo_dep.merged.extend(xd2.merged)
                                yolo_dep.errors.extend(xd2.errors)

                after_health = snapshot_plans(plans)
                health_delta = compare_snapshots(
                    before_health, after_health, apply_summary=apply_summary
                )
                health_paths = write_health_artifacts(
                    before=before_health, after=after_health, delta=health_delta
                )
                history_result = record_apply_history(
                    client,
                    apply_summary=apply_summary,
                    health={
                        "before": before_health.get("totals"),
                        "after": after_health.get("totals"),
                        "delta_open_fixes": health_delta.get("delta_open_fixes"),
                    },
                    dry_run=dry_run or discovery.report_only,
                    skip_profile=skip_profile,
                    mode=mode,
                    sync_remote=not discovery.report_only,
                )
                ledger_rows: list[dict[str, Any]] = []
                if not (dry_run or discovery.report_only):
                    actor = "yolo" if yolo_on else "auto_safe"
                    ledger_rows = record_actions(apply_summary, actor=actor)

                profile_result: ProfileApplyResult | None = None
                if discovery.report_only:
                    profile_result = ProfileApplyResult(
                        action="skipped", detail="report_only"
                    )
                elif not sync_profile:
                    profile_result = ProfileApplyResult(
                        action="skipped", detail="sync_profile_off"
                    )
                else:
                    # Live stars/forks/views + icon rescan + public/private membership.
                    profile_result = sync_profile_readme(
                        client, store, plans, dry_run=bool(dry_run)
                    )

                if yolo_on and yolo_cfg.get("auto_dispatch_agents", True):
                    run_agents = True

                threshold = (
                    float(attention_threshold)
                    if attention_threshold is not None
                    else float(safety.get("attention_threshold_for_agents", 60))
                )
                if run_agents:
                    threshold = 0.0
                max_sessions = int(safety["max_concurrent_agent_sessions"])
                if run_agents:
                    max_sessions = max(
                        max_sessions, len([p for p in plans if p.agent_fixes])
                    )

                dispatch = prepare_dispatches(
                    plans,
                    attention_threshold=threshold,
                    max_sessions=max_sessions
                    if run_agents
                    else int(safety["max_concurrent_agent_sessions"]),
                    max_prompt_chars=int(safety["max_agent_prompt_chars"]),
                )
                if run_agents and not discovery.report_only:
                    dispatch = execute_dispatches(
                        client, store, plans, dispatch, dry_run=dry_run
                    )

                delta_note = (
                    f"Health delta: open fixes {before_health['totals']['open_fixes']}→"
                    f"{after_health['totals']['open_fixes']} "
                    f"(Δ {health_delta['delta_open_fixes']}); "
                    f"mean attention {before_health['totals']['mean_attention']}→"
                    f"{after_health['totals']['mean_attention']}."
                )
                banner = " | ".join(x for x in (report_banner, delta_note) if x)
                target_label = target or profile_login or "portfolio"
                paths = write_artifacts(
                    plans,
                    max_prompt_chars=int(safety["max_agent_prompt_chars"]),
                    report_banner=banner or None,
                    health_delta=health_delta,
                    target_label=target_label,
                    mode=mode,
                    read_only=discovery.report_only,
                )
                md_path = paths["runbook"]
                html_path = paths["report"]
                portfolio_path = paths["portfolio"]

                import json as _json
                import os as _os

                from argus.steward_brief import write_steward_brief

                hotspots_payload: dict = {}
                hs_path = health_paths.get("health_hotspots")
                if hs_path and Path(hs_path).is_file():
                    try:
                        hotspots_payload = _json.loads(
                            Path(hs_path).read_text(encoding="utf-8")
                        )
                    except Exception:  # noqa: BLE001
                        hotspots_payload = {}
                steward_path = write_steward_brief(
                    plans,
                    health_delta=health_delta,
                    hotspots=hotspots_payload,
                    target_label=target_label,
                    mode=mode,
                    pages_url=_os.environ.get("ARGUS_REPORT_URL") or None,
                )
                paths["steward_brief"] = steward_path

                report_sync = {"action": "skipped"}
                if not discovery.report_only:
                    svg_text = None
                    svg_path = health_paths.get("health_infographic_svg")
                    if svg_path and Path(svg_path).is_file():
                        svg_text = Path(svg_path).read_text(encoding="utf-8")
                    report_sync = sync_report_files(
                        client,
                        html=html_path.read_text(encoding="utf-8"),
                        markdown=portfolio_path.read_text(encoding="utf-8"),
                        dry_run=dry_run,
                        steward_html=steward_path.read_text(encoding="utf-8"),
                        infographic_svg=svg_text,
                    )

                digest_result = None
                if yolo_on and not discovery.report_only:
                    extras = list(yolo_extra.digest_notes) if yolo_extra else []
                    items = collect_judgment_items(plans, extras)
                    digest_result = upsert_yolo_digest(
                        client, items, dry_run=dry_run
                    )

                inbox_result = None
                project_result = None
                # Hands-off YOLO: judgment leftovers → one digest Issue only (no per-finding inbox spam).
                if not discovery.report_only and not yolo_on:
                    inbox_result = sync_inbox_issues(
                        client, store, plans, dry_run=dry_run
                    )
                    project_result = sync_inbox_project(client, dry_run=dry_run)
                notify_result = None
                # Quiet posture under YOLO: no creator channel pings (digest + YOLO-OFF / main_red only).
                if notify and not discovery.report_only and not yolo_on:
                    notify_result = send_notifications(plans, report_url=report_url)

                merged_all = list(yolo_merge.merged if yolo_merge else []) + list(
                    yolo_dep.merged if yolo_dep else []
                )
                yolo_errors = list(yolo_extra.errors if yolo_extra else []) + list(
                    yolo_merge.errors if yolo_merge else []
                ) + list(yolo_dep.errors if yolo_dep else [])

                summary = RunSummary(
                    mode=mode,
                    repo_count=len(plans),
                    human_tasks=sum(len(p.human_fixes) for p in plans),
                    agent_repos=len(dispatch.queued),
                    artifacts={
                        "runbook": str(md_path),
                        "report": str(html_path),
                        "portfolio": str(portfolio_path),
                        "portfolio_pages": str(
                            paths.get("portfolio_pages")
                            or (md_path.parent / "portfolio-pages.html")
                        ),
                        "steward_brief": str(steward_path),
                        "status": str(md_path.parent / "status.html"),
                        "inbox_json": str(md_path.parent / "inbox.json"),
                        **health_paths,
                    },
                    details={
                        "new": discovery.new,
                        "removed": discovery.removed,
                        "skipped_archived": discovery.skipped_archived or [],
                        "apply": apply_summary,
                        "health": {
                            "before": before_health["totals"],
                            "after": after_health["totals"],
                            "delta_open_fixes": health_delta["delta_open_fixes"],
                            "delta_mean_attention": health_delta["delta_mean_attention"],
                        },
                        "dispatch": summarize_dispatch(dispatch),
                        "prompt_budget": prompt_budget_report(
                            dispatch.prompts, int(safety["max_agent_prompt_chars"])
                        ),
                        "inbox": None
                        if inbox_result is None
                        else summarize_inbox(inbox_result),
                        "project": None
                        if project_result is None
                        else summarize_project(project_result),
                        "profile": None
                        if profile_result is None
                        else {
                            "action": profile_result.action,
                            "url": profile_result.url,
                            "detail": profile_result.detail,
                            "errors": profile_result.errors,
                        },
                        "notify": None
                        if notify_result is None
                        else {
                            "sent": notify_result.sent,
                            "skipped": notify_result.skipped,
                        },
                        "viewer": discovery.viewer,
                        "report_only": discovery.report_only,
                        "skip_profile": skip_profile,
                        "sync_profile": sync_profile,
                        "github_api": client.quota.snapshot(),
                        "batch": {
                            "max_repos_per_batch": batch_size,
                            "calls_per_repo_estimate": per_repo,
                            "second_pass": second_pass,
                        },
                        "apply_history": {
                            "action": history_result.action,
                            "local_md": history_result.local_md,
                            "local_jsonl": history_result.local_jsonl,
                            "remote_url": history_result.remote_url,
                            "detail": history_result.detail,
                            "errors": history_result.errors,
                        },
                        "report_sync": report_sync,
                        "yolo_digest": None
                        if digest_result is None
                        else {
                            "action": digest_result.action,
                            "url": digest_result.url,
                            "items": digest_result.items,
                            "errors": digest_result.errors,
                        },
                        "yolo": {
                            "enabled": yolo_on,
                            "extras_applied": None
                            if yolo_extra is None
                            else list(yolo_extra.applied),
                            "merged": merged_all,
                            "dependabot_merged": None
                            if yolo_dep is None
                            else list(yolo_dep.merged),
                            "errors": yolo_errors,
                            "second_pass": second_pass,
                        },
                        "action_ledger": {"rows": len(ledger_rows)},
                        "triage": fleet_rollup(plans),
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
                try:
                    import json as _json

                    from argus.paths import DIST_DIR

                    triage_path = DIST_DIR / "triage.json"
                    triage_path.write_text(
                        _json.dumps(summarize_triage(plans), indent=2) + "\n",
                        encoding="utf-8",
                    )
                    summary.artifacts["triage"] = str(triage_path)
                except OSError:
                    pass
                outcome = "dry_run" if dry_run else ("yolo" if yolo_on else "ok")
                emit_run_line(
                    family=mode,
                    plans=plans,
                    checks=len(plans),
                    outcome=outcome,
                )
                return summary
            finally:
                store.close()
    except Exception as exc:
        if notify:
            from argus.notify import send_error_notification

            send_error_notification(str(exc), report_url=report_url)
        raise
