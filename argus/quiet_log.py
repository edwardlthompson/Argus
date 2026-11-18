"""One-line quiet run log (creator posture: no per-finding noise)."""

from __future__ import annotations

from typing import Any


def format_run_line(
    *,
    family: str,
    findings: int,
    files: int,
    checks: int,
    outcome: str,
) -> str:
    return (
        f"argus {family}: findings={findings} files={files} "
        f"checks={checks} outcome={outcome}"
    )


def summarize_plans(plans: list[Any]) -> tuple[int, int]:
    findings = 0
    for plan in plans:
        findings += len(getattr(plan, "human_fixes", []) or [])
        findings += len(getattr(plan, "agent_fixes", []) or [])
        findings += len(getattr(plan, "auto_fixes", []) or [])
    return findings, len(plans)


def emit_run_line(
    *,
    family: str,
    plans: list[Any],
    checks: int,
    outcome: str,
) -> str:
    findings, files = summarize_plans(plans)
    line = format_run_line(
        family=family,
        findings=findings,
        files=files,
        checks=checks,
        outcome=outcome,
    )
    print(line)
    return line
