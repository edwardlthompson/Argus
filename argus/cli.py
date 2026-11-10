"""Argus CLI."""

from __future__ import annotations

import json
import sys

import click
import yaml

from argus import __version__
from argus.config_loader import (
    ConfigError,
    load_allowlist,
    load_fixes,
    load_inbox,
    load_notifications,
    load_rubric,
    load_safety,
    load_status,
)
from argus.inbox_guard import check_public_controller_risks
from argus.models import RepoStatus
from argus.paths import CONFIG_DIR, PROJECT_ROOT, ensure_runtime_dirs
from argus.pipeline import run_pipeline
from argus.state import StateStore


@click.group()
@click.version_option(__version__, prog_name="argus")
def main() -> None:
    """Argus — multi-repo hygiene controller."""


@main.command("run")
@click.option(
    "--dry-run/--apply",
    default=None,
    help="Dry-run vs apply. When apply_mode=yolo and neither flag is set, apply is implied.",
)
@click.option("--profile", default="generic", show_default=True)
@click.option("--no-notify", is_flag=True, default=False)
@click.option("--report-url", default=None, help="Public URL to HTML report for notifications")
@click.option("--include-archived", is_flag=True, default=False)
@click.option(
    "--skip-profile/--with-profile",
    default=None,
    help="Skip USERNAME/USERNAME Overview. YOLO defaults to skip; --with-profile forces sync.",
)
def run_cmd(
    dry_run: bool | None,
    profile: str,
    no_notify: bool,
    report_url: str | None,
    include_archived: bool,
    skip_profile: bool | None,
) -> None:
    """Full silent/scheduled run (archived repos skipped by default)."""
    ensure_runtime_dirs()
    summary = run_pipeline(
        dry_run=dry_run,
        profile=profile,
        notify=not no_notify,
        report_url=report_url,
        include_archived=include_archived,
        skip_profile=skip_profile,
    )
    effective_dry = summary.details.get("apply", {}).get("dry_run")
    click.echo(json.dumps({
        "mode": summary.mode,
        "repos": summary.repo_count,
        "human_tasks": summary.human_tasks,
        "skipped_archived": summary.details.get("skipped_archived"),
        "health": summary.details.get("health"),
        "yolo": summary.details.get("yolo"),
        "artifacts": summary.artifacts,
        "dry_run": dry_run if dry_run is not None else (summary.mode == "run"),
        "effective_dry_run_hint": effective_dry,
    }, indent=2))


@main.command("fix")
@click.option(
    "--dry-run/--apply",
    default=None,
    help="Dry-run vs apply. When apply_mode=yolo and neither flag is set, apply is implied.",
)
@click.option("--agent", "run_agents", is_flag=True, default=False, help="Batch agent dispatch")
@click.option("--profile", default="generic", show_default=True)
@click.option("--include-archived", is_flag=True, default=False)
@click.option("--no-notify", is_flag=True, default=False)
@click.option("--report-url", default=None)
@click.option("--repo", "repos", multiple=True, help="Limit to owner/name (repeatable)")
@click.option(
    "--skip-profile/--with-profile",
    default=None,
    help="Skip USERNAME/USERNAME Overview. YOLO defaults to skip; --with-profile forces sync.",
)
def fix_cmd(
    dry_run: bool | None,
    run_agents: bool,
    profile: str,
    include_archived: bool,
    no_notify: bool,
    report_url: str | None,
    repos: tuple[str, ...],
    skip_profile: bool | None,
) -> None:
    """Apply auto_safe fixes across the portfolio (and optionally agents)."""
    ensure_runtime_dirs()
    summary = run_pipeline(
        dry_run=dry_run,
        profile=profile,
        notify=not no_notify,
        report_url=report_url,
        include_archived=include_archived,
        run_agents=run_agents,
        attention_threshold=0.0 if run_agents else None,
        skip_profile=skip_profile,
    )
    # Optional post-filter messaging when --repo used (full scan still for scoring consistency)
    details = summary.details
    if repos:
        wanted = set(repos)
        details = {**details, "repo_filter": sorted(wanted)}
    click.echo(json.dumps({
        "mode": summary.mode,
        "repos": summary.repo_count,
        "human_tasks": summary.human_tasks,
        "apply": details.get("apply"),
        "health": details.get("health"),
        "apply_history": details.get("apply_history"),
        "github_api": details.get("github_api"),
        "profile": details.get("profile"),
        "dispatch": details.get("dispatch"),
        "artifacts": summary.artifacts,
        "yolo": details.get("yolo"),
        "dry_run": dry_run,
        "agent": run_agents,
    }, indent=2))


@main.command("report")
@click.option("--target", required=True, help="user | user/repo | org")
@click.option("--public-only", is_flag=True, default=False)
@click.option("--profile", default="generic", show_default=True)
@click.option("--include-archived", is_flag=True, default=False)
@click.option("--open", "open_html", is_flag=True, default=False, help="Open local report.html")
def report_cmd(
    target: str, public_only: bool, profile: str, include_archived: bool, open_html: bool
) -> None:
    """Read-only scan of one user/org/repo."""
    ensure_runtime_dirs()
    summary = run_pipeline(
        dry_run=True,
        target=target,
        public_only=public_only,
        profile=profile,
        notify=False,
        include_archived=include_archived,
    )
    click.echo(json.dumps({
        "mode": summary.mode,
        "repos": summary.repo_count,
        "human_tasks": summary.human_tasks,
        "artifacts": summary.artifacts,
        "report_only": True,
    }, indent=2))
    if open_html:
        import webbrowser
        from pathlib import Path

        html = Path(summary.artifacts.get("report") or "")
        if html.is_file():
            webbrowser.open(html.resolve().as_uri())


@main.command("status")
@click.option("--safe", is_flag=True, default=False, help="Print public-safe counts from dist/status.json")
def status_cmd(safe: bool) -> None:
    """Portfolio overview from local state + status.yaml (or --safe counts)."""
    from argus.paths import DIST_DIR

    if safe:
        path = DIST_DIR / "status.json"
        if not path.exists():
            click.echo(json.dumps({"error": "no status.json — run argus run first"}))
            return
        click.echo(path.read_text(encoding="utf-8"))
        return
    declared = load_status()
    store = StateStore()
    try:
        known = store.known_repos()
        rows = []
        names = sorted(set(declared) | set(known))
        for name in names:
            st = declared.get(name) or (known[name]["status"] if name in known else RepoStatus.ACTIVE)
            active = known.get(name, {}).get("active", True)
            rows.append({"repo": name, "status": st.value if hasattr(st, "value") else st, "active": active})
        click.echo(json.dumps(rows, indent=2))
    finally:
        store.close()


@main.command("inbox")
@click.option("--dry-run/--apply", default=True, show_default=True)
def inbox_cmd(dry_run: bool) -> None:
    """List/sync argus-inbox Issues (dry-run default)."""
    import os

    from argus.github_client import GitHubClient
    from argus.inbox_issues import sync_inbox_issues

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set")
    store = StateStore()
    try:
        with GitHubClient(token=token) as client:
            result = sync_inbox_issues(client, store, plans=[], dry_run=dry_run)
        click.echo(json.dumps({
            "dry_run": dry_run,
            "created": result.created,
            "updated": result.updated,
            "resolved": result.resolved,
            "errors": result.errors,
        }, indent=2))
    finally:
        store.close()


def _set_status(full_name: str, status: RepoStatus) -> None:
    path = CONFIG_DIR / "status.yaml"
    data: dict = {"repos": {}}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {"repos": {}}
    data.setdefault("repos", {})[full_name] = {"status": status.value}
    path.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")
    store = StateStore()
    try:
        store.set_status(full_name, status)
    finally:
        store.close()


@main.command("park")
@click.argument("repo")
def park_cmd(repo: str) -> None:
    """Mark a repository as parked."""
    _set_status(repo, RepoStatus.PARKED)
    click.echo(f"parked {repo}")


@main.command("unpark")
@click.argument("repo")
def unpark_cmd(repo: str) -> None:
    """Mark a repository as active."""
    _set_status(repo, RepoStatus.ACTIVE)
    click.echo(f"unparked {repo}")


@main.command("status-set")
@click.argument("repo")
@click.argument("status", type=click.Choice([s.value for s in RepoStatus]))
def status_set_cmd(repo: str, status: str) -> None:
    """Set repository status explicitly."""
    _set_status(repo, RepoStatus(status))
    click.echo(f"{repo} -> {status}")


@main.command("allow")
@click.argument("repo")
def allow_cmd(repo: str) -> None:
    """Add a repository to the allow-list."""
    path = CONFIG_DIR / "allowlist.yaml"
    data = load_allowlist()
    allow = list(data.get("allow") or [])
    if repo not in allow:
        allow.append(repo)
    payload = {"mode": data.get("mode", "owner_only"), "allow": allow, "deny": data.get("deny") or []}
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    click.echo(f"allowed {repo}")


@main.command("explain")
@click.argument("repo")
def explain_cmd(repo: str) -> None:
    """Dump attention-score breakdown for owner/name (read-only)."""
    import os

    from argus.explain import explain_repo
    from argus.github_client import GitHubClient

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set")
    with GitHubClient(token=token, report_only=True) as client:
        click.echo(json.dumps(explain_repo(client, repo), indent=2))


@main.command("history")
@click.option("--limit", default=20, show_default=True)
def history_cmd(limit: int) -> None:
    """Show recent run history."""
    store = StateStore()
    try:
        click.echo(json.dumps(store.history(limit), indent=2))
    finally:
        store.close()


@main.command("doctor")
def doctor_cmd() -> None:
    """Check token, config validity, and safety settings."""
    import os
    import smtplib

    problems: list[str] = []
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        problems.append("GITHUB_TOKEN is not set")

    try:
        fixes = load_fixes()
        click.echo(f"fixes: {len(fixes)} loaded")
    except ConfigError as exc:
        problems.append(f"fixes.yaml: {exc}")

    try:
        load_rubric()
        click.echo("rubric: ok")
    except ConfigError as exc:
        problems.append(f"rubric.yaml: {exc}")

    try:
        load_status()
        click.echo("status: ok")
    except ConfigError as exc:
        problems.append(f"status.yaml: {exc}")

    try:
        notif = load_notifications()
        click.echo("notifications: ok")
        for ch in ("discord", "telegram", "webhook", "email"):
            enabled = bool((notif.get(ch) or {}).get("enabled"))
            click.echo(f"  channel {ch}: {'enabled' if enabled else 'off'}")
        email = notif.get("email") or {}
        if email.get("enabled") and email.get("smtp_host"):
            try:
                with smtplib.SMTP(str(email["smtp_host"]), int(email.get("smtp_port") or 587), timeout=5) as smtp:
                    if email.get("use_tls", True):
                        smtp.starttls()
                click.echo("email smtp: reachable")
            except Exception as exc:  # noqa: BLE001
                problems.append(f"email smtp smoke failed: {exc}")
    except ConfigError as exc:
        problems.append(f"notifications.yaml: {exc}")

    safety = load_safety()
    click.echo(f"safety: {json.dumps(safety)}")
    click.echo(f"apply_mode: {safety.get('apply_mode', 'normal')}")
    api = safety.get("github_api") or {}
    click.echo(
        "github_api: "
        f"hint={api.get('core_limit_hint')} reserve={api.get('reserve')} "
        f"batch={api.get('max_repos_per_batch')} est_calls/repo={api.get('calls_per_repo_estimate')}"
    )
    if token:
        try:
            from argus.github_client import GitHubClient
            from argus.pipeline import _quota_from_safety

            with GitHubClient(token=token, report_only=True, quota=_quota_from_safety(safety)) as gh:
                live = gh.refresh_rate_limit()
                core = (live.get("resources") or {}).get("core") or {}
                click.echo(
                    f"github_core_live: limit={core.get('limit')} "
                    f"remaining={core.get('remaining')} reset={core.get('reset')}"
                )
                if int(core.get("remaining") or 0) < int(api.get("reserve") or 250):
                    problems.append(
                        "GitHub core remaining below reserve — wait for reset before a full scan"
                    )
        except Exception as exc:  # noqa: BLE001
            problems.append(f"github rate_limit check failed: {exc}")

    required = ("never_delete_repos", "never_force_push", "prefer_pull_requests")
    for key in required:
        if not safety.get(key, True):
            problems.append(f"safety.yaml disables hard safety default: {key}")

    from argus.grok_budget import breaker_open, load_grok_config
    from argus.yolo_arm import is_yolo_armed, yolo_off_marker, yolo_on_path

    armed = is_yolo_armed(safety)
    click.echo(
        f"yolo_arm: {'armed' if armed else 'off'} "
        f"(yolo.on={yolo_on_path().is_file()} YOLO-OFF={yolo_off_marker().is_file()} "
        f"apply_mode={safety.get('apply_mode', 'normal')})"
    )
    if armed:
        click.echo("yolo: enabled (see docs/YOLO.md) — hard floors still required")
        yolo = safety.get("yolo") or {}
        try:
            cap = int(yolo.get("max_auto_merges_per_day") or 0)
        except (TypeError, ValueError):
            cap = 0
        if cap < 1:
            problems.append("yolo.max_auto_merges_per_day must be >= 1 when YOLO is armed")

    grok_cfg = load_grok_config()
    click.echo(
        f"grok_budget: enabled={bool(grok_cfg.get('enabled', True))} "
        f"max_runs/day={grok_cfg.get('max_total_bot_runs_per_day')} "
        f"token_cap={grok_cfg.get('max_estimated_tokens_per_day')} "
        f"breaker={'OPEN' if breaker_open(grok_cfg) else 'closed'}"
    )
    from argus.ux.rollout import load_config as load_ux_rollout_cfg
    from argus.ux.rollout import load_state as load_ux_rollout_state

    ux_cfg = load_ux_rollout_cfg()
    ux_st = load_ux_rollout_state()
    click.echo(
        f"ux_rollout: default={ux_cfg.get('default_stage')} "
        f"rules_tracked={len(ux_st.get('rules') or {})}"
    )
    if os.environ.get("RELEASE_TOKEN") or os.environ.get("ARGUS_RELEASE_TOKEN"):
        click.echo("release_token: set")
    else:
        click.echo("release_token: missing (SEC-RELEASE-TOKEN-MISSING when release workflows exist)")

    allow = load_allowlist()
    click.echo(f"allowlist mode: {allow.get('mode')}")

    try:
        inbox = load_inbox()
        click.echo(f"inbox controller: {inbox.get('controller_repo')}")
    except ConfigError as exc:
        problems.append(f"inbox.yaml: {exc}")
        inbox = {}

    client = None
    if token:
        try:
            from argus.github_client import GitHubClient

            client = GitHubClient(token=token)
            me = client.whoami()
            click.echo(f"github: authenticated as {me.get('login')}")
            for warn in check_public_controller_risks(client, config=inbox):
                problems.append(warn)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"github auth failed: {exc}")
            for warn in check_public_controller_risks(None, config=inbox):
                problems.append(warn)
    elif inbox.get("security_issues"):
        for warn in check_public_controller_risks(None, config=inbox):
            problems.append(warn)

    if client is not None:
        client.close()

    if problems:
        for p in problems:
            click.echo(f"PROBLEM: {p}", err=True)
        raise SystemExit(1)
    click.echo("doctor: all checks passed")
    click.echo(f"root: {PROJECT_ROOT}")


@main.command("cost")
def cost_cmd() -> None:
    """Report Argus action + Grok budget counters."""
    from argus.cost import report

    click.echo(json.dumps(report(), indent=2))


@main.command("off")
@click.argument("reason")
def off_cmd(reason: str) -> None:
    """Disarm YOLO + remote (sticky ARGUS-OFF.md)."""
    from argus.remote import argus_off

    click.echo(json.dumps(argus_off(reason), indent=2))


@main.command("digest")
@click.option("--from-dist", is_flag=True, default=True, show_default=True)
def digest_cmd(from_dist: bool) -> None:
    """Show last triage/yolo digest summary from dist/."""
    from argus.paths import DIST_DIR

    triage = DIST_DIR / "triage.json"
    if from_dist and triage.is_file():
        data = json.loads(triage.read_text(encoding="utf-8"))
        click.echo(json.dumps({
            "counts": data.get("counts"),
            "human": (data.get("by_class") or {}).get("human", [])[:20],
            "agent": (data.get("by_class") or {}).get("agent", [])[:20],
        }, indent=2))
        return
    raise SystemExit("no dist/triage.json — run argus run first")


@main.command("focus")
@click.argument("fix_id")
@click.option("--from-dist", is_flag=True, default=True)
def focus_cmd(fix_id: str, from_dist: bool) -> None:
    """List repos matching one fix id from last triage."""
    from argus.paths import DIST_DIR

    path = DIST_DIR / "triage.json"
    if not (from_dist and path.is_file()):
        raise SystemExit("no dist/triage.json — run argus run first")
    data = json.loads(path.read_text(encoding="utf-8"))
    repos = (data.get("by_fix_id") or {}).get(fix_id) or []
    click.echo(json.dumps({"fix_id": fix_id, "repos": repos}, indent=2))


@main.group("fleet")
def fleet_group() -> None:
    """Fleet upgrade-wave rails (plan / execute / drift / revert / halt)."""


@fleet_group.command("plan")
@click.argument("brief_id")
@click.option("--repo", "repos", multiple=True, required=True)
@click.option("--verify", required=True, help="Mandatory verify command")
@click.option("--auto", is_flag=True, default=False)
def fleet_plan_cmd(brief_id: str, repos: tuple[str, ...], verify: str, auto: bool) -> None:
    from argus.fleet import write_plan

    path = write_plan(brief_id, list(repos), verify=verify, auto=auto)
    click.echo(json.dumps({"plan": str(path), "repos": list(repos)}, indent=2))


@fleet_group.command("execute")
@click.argument("brief_id")
@click.option("--approve", is_flag=True, default=False)
@click.option("--no-wait-checks", is_flag=True, default=False)
def fleet_execute_cmd(brief_id: str, approve: bool, no_wait_checks: bool) -> None:
    import os

    from argus.fleet_exec import execute_plan
    from argus.github_client import GitHubClient

    client = None
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ARGUS_GITHUB_TOKEN") or ""
    if approve and token:
        client = GitHubClient(token=token)
    try:
        click.echo(json.dumps(
            execute_plan(
                brief_id,
                approve=approve,
                client=client,
                wait_checks=not no_wait_checks,
            ),
            indent=2,
        ))
    finally:
        if client is not None:
            client.close()


@fleet_group.command("drift")
@click.argument("brief_id")
def fleet_drift_cmd(brief_id: str) -> None:
    from argus.fleet_exec import drift_report

    click.echo(json.dumps(drift_report(brief_id), indent=2))


@fleet_group.command("revert")
@click.argument("brief_id")
@click.option("--apply", "do_apply", is_flag=True, default=False)
def fleet_revert_cmd(brief_id: str, do_apply: bool) -> None:
    from argus.fleet import revert_brief

    click.echo(json.dumps(revert_brief(brief_id, dry_run=not do_apply), indent=2))


@fleet_group.command("halt")
@click.argument("reason")
def fleet_halt_cmd(reason: str) -> None:
    from argus.fleet import halt

    click.echo(json.dumps({"halt": str(halt(reason))}, indent=2))


@main.group("rules")
def rules_group() -> None:
    """Parent rule sync (pin / diff / bump)."""


@rules_group.command("diff")
def rules_diff_cmd() -> None:
    """Show locked vs current rules tree sha."""
    from argus.rules_sync import status_payload

    click.echo(json.dumps(status_payload(), indent=2))


@rules_group.command("sync")
def rules_sync_cmd() -> None:
    """Refresh argus.rules.lock to the current local rules tree."""
    from argus.rules_sync import sync_lock

    click.echo(json.dumps(sync_lock(), indent=2))


@rules_group.command("bump")
@click.argument("ref")
def rules_bump_cmd(ref: str) -> None:
    """Pin argus.upstream.json to REF (mode=pinned)."""
    from argus.rules_sync import bump_ref, status_payload

    bump_ref(ref)
    click.echo(json.dumps(status_payload(), indent=2))


@main.command("triage")
@click.option("--fleet", is_flag=True, default=False, help="Cross-repo rollup by fix id")
@click.option("--profile", default="generic", show_default=True)
@click.option(
    "--from-dist",
    is_flag=True,
    default=False,
    help="Read dist/triage.json from last run (no network)",
)
def triage_cmd(fleet: bool, profile: str, from_dist: bool) -> None:
    """Group open fixes by class (agent / human / auto_safe)."""
    from argus.paths import DIST_DIR

    ensure_runtime_dirs()
    triage_path = DIST_DIR / "triage.json"
    if from_dist:
        if not triage_path.is_file():
            raise SystemExit("no dist/triage.json — run argus run/fix first")
        data = json.loads(triage_path.read_text(encoding="utf-8"))
        if fleet:
            click.echo(json.dumps({
                "mode": "fleet",
                "repos": data.get("repos"),
                "counts": data.get("counts"),
                "by_fix_id": data.get("by_fix_id"),
                "agent_deterministic_count": len(data.get("yolo_eligible_agent") or []),
                "human_count": (data.get("counts") or {}).get("human", 0),
                "auto_safe_count": (data.get("counts") or {}).get("auto_safe", 0),
            }, indent=2))
        else:
            click.echo(json.dumps(data, indent=2))
        return
    summary = run_pipeline(
        dry_run=True,
        profile=profile,
        notify=False,
        include_archived=False,
    )
    payload = summary.details.get("triage") or {}
    if not fleet and triage_path.is_file():
        payload = json.loads(triage_path.read_text(encoding="utf-8"))
    click.echo(json.dumps(payload, indent=2))


@main.command()
def completion() -> None:
    """Print shell completion setup hint for Click."""
    click.echo(
        "PowerShell: argus completion | Out-File -Encoding utf8 argus.ps1; . ./argus.ps1\n"
        "bash: eval \"$(_ARGUS_COMPLETE=bash_source argus)\"\n"
        "See https://click.palletsprojects.com/shell-completion/"
    )


# Alias so `argus status <repo> experimental` can be documented; Click groups conflict,
# so we expose status-set and keep `status` for overview.
main.add_command(status_set_cmd, name="set-status")


if __name__ == "__main__":
    sys.exit(main())
