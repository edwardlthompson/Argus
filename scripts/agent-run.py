#!/usr/bin/env python3
"""Thin Argus agent-run shim — maps template verbs without full bootstrap lifecycle."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VERIFY_VERBS = frozenset(
    {
        "verify",
        "validate-bootstrap",
        "watch-agent-gates",
        "smoke-sprint",
        "check-repo-hygiene",
        "render-gates-status",
        "project-health",
        "tour-verify",
        "check-readme-health",
        "feedback-inbox",
        "feature-autofix",
    }
)

NA_VERBS = frozenset(
    {
        "feature-gate",
        "check-local-compute",
        "check-parallel-scope",
        "plan-parallel-dispatch",
        "gc-parallel-lock",
        "attempt-build-plan-row",
        "set-parallel-sprint-done",
        "simulate-template-upgrade",
        "check-template-updates",
        "check-template-gaps",
        "update-deps",
        "render-upd-status",
        "apply-depsonar-gradle",
        "pre-release-gate",
        "prerelease-autofix",
        "release-please-dry",
        "merge-release-please-pr",
        "check-github-ci",
        "check-changelog-unreleased",
        "wait-release-sbom",
        "check-pages-analytics",
        "sync-open-prs-build-plan",
        "cursor-feature-radar",
        "copy-sandbox-config",
        "install-commit-msg-hook",
        "validate-template-index",
        "run-android-emulator-local",
        "check-espresso-android16",
        "resume-handoff",
    }
)


def _run_verify() -> int:
    if sys.platform == "win32":
        script = ROOT / "scripts" / "verify.ps1"
        cmd = ["powershell", "-NoProfile", "-File", str(script)]
    else:
        script = ROOT / "scripts" / "verify.sh"
        cmd = ["bash", str(script)]
    return subprocess.call(cmd, cwd=str(ROOT))


def _next_build_plan_row() -> str:
    path = ROOT / "BUILD_PLAN.md"
    if not path.is_file():
        return "(no BUILD_PLAN.md)"
    for line in path.read_text(encoding="utf-8").splitlines():
        if "🔲" in line and "[AGENT]" in line:
            return line.strip()
    return "(no open AGENT rows)"


def _smoke_hooks() -> int:
    hooks_dir = ROOT / ".cursor" / "hooks"
    required = [
        "before_shell_guard.py",
        "after_edit_encoding.py",
        "session_start_context.py",
        "shell-denylist.txt",
    ]
    missing = [n for n in required if not (hooks_dir / n).is_file()]
    if missing:
        print(f"FAIL check-cursor-hooks — missing {missing}")
        return 1
    # Import-compile guard modules (fail-open scripts should still parse)
    for name in ("before_shell_guard", "after_edit_encoding", "session_start_context"):
        path = hooks_dir / f"{name}.py"
        src = path.read_text(encoding="utf-8")
        compile(src, str(path), "exec")
    print("OK check-cursor-hooks --smoke")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print("Argus agent-run shim")
        print("VERIFY:", ", ".join(sorted(VERIFY_VERBS)))
        print("N/A:", ", ".join(sorted(NA_VERBS)))
        print("Special: check-cursor-hooks, build-sprint-status (prints next row)")
        return 0

    verb = argv[0]
    # strip leading dashes used by some wrappers
    if verb.startswith("--"):
        verb = verb.lstrip("-")

    if verb == "check-cursor-hooks":
        return _smoke_hooks()

    if verb == "build-sprint-status":
        print(_next_build_plan_row())
        return 0

    if verb in VERIFY_VERBS:
        return _run_verify()

    if verb in NA_VERBS:
        print(f"Argus child: N/A — {verb} (PARENT_GAP_LIST G12)")
        return 0

    print(f"Argus child: unknown verb {verb!r} — extend VERIFY_VERBS or NA_VERBS", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
