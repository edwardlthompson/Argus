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
    load_notifications,
    load_rubric,
    load_safety,
    load_status,
)
from argus.models import RepoStatus
from argus.paths import CONFIG_DIR, PROJECT_ROOT, ensure_runtime_dirs
from argus.pipeline import run_pipeline
from argus.state import StateStore


@click.group()
@click.version_option(__version__, prog_name="argus")
def main() -> None:
    """Argus — multi-repo hygiene controller."""


@main.command("run")
@click.option("--dry-run/--apply", default=True, show_default=True)
@click.option("--profile", default="generic", show_default=True)
@click.option("--no-notify", is_flag=True, default=False)
@click.option("--report-url", default=None, help="Public URL to HTML report for notifications")
@click.option("--include-archived", is_flag=True, default=False)
def run_cmd(
    dry_run: bool,
    profile: str,
    no_notify: bool,
    report_url: str | None,
    include_archived: bool,
) -> None:
    """Full silent/scheduled run (archived repos skipped by default)."""
    ensure_runtime_dirs()
    summary = run_pipeline(
        dry_run=dry_run,
        profile=profile,
        notify=not no_notify,
        report_url=report_url,
        include_archived=include_archived,
    )
    click.echo(json.dumps({
        "mode": summary.mode,
        "repos": summary.repo_count,
        "human_tasks": summary.human_tasks,
        "skipped_archived": summary.details.get("skipped_archived"),
        "artifacts": summary.artifacts,
        "dry_run": dry_run,
    }, indent=2))


@main.command("fix")
@click.option("--dry-run/--apply", default=True, show_default=True)
@click.option("--agent", "run_agents", is_flag=True, default=False, help="Batch agent dispatch")
@click.option("--profile", default="generic", show_default=True)
@click.option("--include-archived", is_flag=True, default=False)
@click.option("--no-notify", is_flag=True, default=False)
@click.option("--report-url", default=None)
@click.option("--repo", "repos", multiple=True, help="Limit to owner/name (repeatable)")
def fix_cmd(
    dry_run: bool,
    run_agents: bool,
    profile: str,
    include_archived: bool,
    no_notify: bool,
    report_url: str | None,
    repos: tuple[str, ...],
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
        "dispatch": details.get("dispatch"),
        "artifacts": summary.artifacts,
        "dry_run": dry_run,
        "agent": run_agents,
    }, indent=2))


@main.command("report")
@click.option("--target", required=True, help="user | user/repo | org")
@click.option("--public-only", is_flag=True, default=False)
@click.option("--profile", default="generic", show_default=True)
@click.option("--include-archived", is_flag=True, default=False)
def report_cmd(
    target: str, public_only: bool, profile: str, include_archived: bool
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


@main.command("status")
def status_cmd() -> None:
    """Portfolio overview from local state + status.yaml."""
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
        load_notifications()
        click.echo("notifications: ok")
    except ConfigError as exc:
        problems.append(f"notifications.yaml: {exc}")

    safety = load_safety()
    click.echo(f"safety: {json.dumps(safety)}")

    required = ("never_delete_repos", "never_force_push", "prefer_pull_requests")
    for key in required:
        if not safety.get(key, True):
            problems.append(f"safety.yaml disables hard safety default: {key}")

    allow = load_allowlist()
    click.echo(f"allowlist mode: {allow.get('mode')}")

    if token:
        try:
            from argus.github_client import GitHubClient

            with GitHubClient(token=token) as client:
                me = client.whoami()
                click.echo(f"github: authenticated as {me.get('login')}")
        except Exception as exc:  # noqa: BLE001
            problems.append(f"github auth failed: {exc}")

    if problems:
        for p in problems:
            click.echo(f"PROBLEM: {p}", err=True)
        raise SystemExit(1)
    click.echo("doctor: all checks passed")
    click.echo(f"root: {PROJECT_ROOT}")


# Alias so `argus status <repo> experimental` can be documented; Click groups conflict,
# so we expose status-set and keep `status` for overview.
main.add_command(status_set_cmd, name="set-status")


if __name__ == "__main__":
    sys.exit(main())
