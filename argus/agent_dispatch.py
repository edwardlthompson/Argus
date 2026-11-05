"""Gated agentic dispatch with circuit breaker and optional worktree execution."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from argus.agent_ops import open_gate_failure_issue
from argus.compose import _agent_prompt_block
from argus.config_loader import load_yaml
from argus.github_client import GitHubClient, GitHubError
from argus.models import FixClass, RepoPlan
from argus.paths import CONFIG_DIR, DATA_DIR, ensure_runtime_dirs
from argus.state import StateStore


@dataclass
class DispatchResult:
    queued: list[str] = field(default_factory=list)
    paused: bool = False
    reason: str | None = None
    prompts: dict[str, str] = field(default_factory=dict)
    executed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    mechanical: list[str] = field(default_factory=list)


class CircuitBreaker:
    def __init__(self, max_failures: int = 2) -> None:
        self.max_failures = max_failures
        self.failures = 0
        self.open = False

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.max_failures:
            self.open = True

    def record_success(self) -> None:
        self.failures = 0
        self.open = False


def _agent_cfg() -> dict[str, Any]:
    path = CONFIG_DIR / "agent.yaml"
    if not path.exists():
        return {"enabled": True, "mechanical_fallback": True, "command": [], "max_concurrent": 1}
    return load_yaml(path)


def prepare_dispatches(
    plans: list[RepoPlan],
    *,
    attention_threshold: float = 0.0,
    max_sessions: int = 1,
    max_prompt_chars: int = 12000,
    breaker: CircuitBreaker | None = None,
) -> DispatchResult:
    """Queue agent prompts. Default threshold 0 so `argus fix --agent` can batch hygiene."""
    breaker = breaker or CircuitBreaker()
    result = DispatchResult()
    if breaker.open:
        result.paused = True
        result.reason = "circuit_breaker_open"
        return result

    candidates = [
        p
        for p in plans
        if p.agent_fixes and not p.report_only and p.score.attention >= attention_threshold
    ]
    candidates.sort(key=lambda p: p.score.attention, reverse=True)

    for plan in candidates[:max_sessions]:
        block, _deferred = _agent_prompt_block(
            plan.repo.full_name, plan.agent_fixes, max_chars=max_prompt_chars
        )
        result.queued.append(plan.repo.full_name)
        result.prompts[plan.repo.full_name] = block
    return result


def _mechanical_memory_layout(workdir: Path) -> bool:
    src = workdir / "AGENT_MEMORY.md"
    if not src.exists():
        return False
    dest_dir = workdir / ".agent"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "AGENT_MEMORY.md"
    if not dest.exists():
        shutil.move(str(src), str(dest))
        return True
    return False


def execute_dispatches(
    client: GitHubClient,
    store: StateStore,
    plans: list[RepoPlan],
    dispatch: DispatchResult,
    *,
    dry_run: bool = True,
) -> DispatchResult:
    """Clone/worktree + run agent command, or mechanical fallback. Opens PRs when possible."""
    cfg = _agent_cfg()
    if not cfg.get("enabled", True):
        dispatch.reason = "agent_disabled"
        return dispatch
    if dry_run:
        return dispatch

    ensure_runtime_dirs()
    root = DATA_DIR / "worktrees"
    root.mkdir(parents=True, exist_ok=True)
    by_name = {p.repo.full_name: p for p in plans}

    for full in list(dispatch.queued):
        plan = by_name.get(full)
        if not plan or not plan.repo.can_write:
            continue
        slug = full.replace("/", "__")
        workdir = root / slug
        try:
            if workdir.exists():
                shutil.rmtree(workdir)
            # Shallow clone via git
            url = f"https://github.com/{full}.git"
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(workdir)],
                check=True,
                capture_output=True,
                text=True,
            )
            prompt_dir = workdir / ".argus"
            prompt_dir.mkdir(parents=True, exist_ok=True)
            prompt_file = prompt_dir / "prompt.md"
            prompt_file.write_text(dispatch.prompts.get(full, ""), encoding="utf-8")

            cmd = list(cfg.get("command") or [])
            ran_agent = False
            if cmd:
                filled = [
                    c.format(workdir=str(workdir), prompt_file=str(prompt_file), repo=full)
                    for c in cmd
                ]
                proc = subprocess.run(filled, cwd=str(workdir), capture_output=True, text=True)
                ran_agent = proc.returncode == 0
                if not ran_agent:
                    dispatch.errors.append(f"{full}:agent_exit_{proc.returncode}")

            mechanical = False
            if (not ran_agent) and cfg.get("mechanical_fallback", True):
                if any(m.fix.id == "AGENT-MEMORY-LAYOUT" for m in plan.agent_fixes):
                    mechanical = _mechanical_memory_layout(workdir)
                    if mechanical:
                        dispatch.mechanical.append(full)

            if ran_agent or mechanical:
                # Commit + push branch + PR via gh if available
                branch = "chore/argus-agent"
                subprocess.run(["git", "checkout", "-B", branch], cwd=str(workdir), check=False)
                subprocess.run(["git", "add", "-A"], cwd=str(workdir), check=False)
                subprocess.run(
                    ["git", "commit", "-m", "chore(argus): gated agent / mechanical fixes"],
                    cwd=str(workdir),
                    check=False,
                )
                push = subprocess.run(
                    ["git", "push", "-u", "origin", branch],
                    cwd=str(workdir),
                    capture_output=True,
                    text=True,
                )
                if push.returncode == 0:
                    try:
                        client.post(
                            f"/repos/{plan.repo.owner}/{plan.repo.name}/pulls",
                            allow_write=True,
                            json={
                                "title": "chore(argus): agent batch fixes",
                                "head": branch,
                                "base": plan.repo.default_branch,
                                "body": "Opened by Argus agent dispatch.\n\n"
                                + ", ".join(m.fix.id for m in plan.agent_fixes),
                            },
                        )
                        for m in plan.agent_fixes:
                            if m.fix.class_ == FixClass.AGENT and (
                                ran_agent or m.fix.id == "AGENT-MEMORY-LAYOUT"
                            ):
                                store.record_resolution(
                                    full,
                                    m.fix.id,
                                    ttl_days=m.fix.resolution_ttl_days or 30,
                                    source="agent_dispatch",
                                )
                        dispatch.executed.append(full)
                    except GitHubError as exc:
                        dispatch.errors.append(f"{full}:pr:{exc}")
                else:
                    dispatch.errors.append(f"{full}:push_failed")
        except Exception as exc:  # noqa: BLE001
            dispatch.errors.append(f"{full}:{exc}")
        finally:
            if workdir.exists() and cfg.get("cleanup_worktrees", True):
                shutil.rmtree(workdir, ignore_errors=True)
    if dispatch.errors and not dry_run:
        try:
            open_gate_failure_issue(
                client,
                title=f"Argus gate failures ({len(dispatch.errors)})",
                body="\n".join(f"- `{e}`" for e in dispatch.errors[:20]),
                dry_run=False,
            )
        except GitHubError as exc:
            dispatch.errors.append(f"gate_issue:{exc}")
    return dispatch


def mark_merged_fixes(store: StateStore, repo: str, fix_ids: list[str], ttl_days: int = 30) -> None:
    for fid in fix_ids:
        store.record_resolution(repo, fid, ttl_days=ttl_days, source="agent_pr_merged")


def summarize_dispatch(result: DispatchResult) -> dict[str, Any]:
    return {
        "queued": result.queued,
        "paused": result.paused,
        "reason": result.reason,
        "prompt_repos": list(result.prompts.keys()),
        "executed": result.executed,
        "mechanical": result.mechanical,
        "errors": result.errors,
        "circuit_open": result.paused and result.reason == "circuit_breaker_open",
    }
