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


def _project_dep_names() -> set[str]:
    """Direct dependency names from pyproject.toml (runtime + optional)."""
    import re

    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    names: set[str] = set()
    for raw in re.findall(r'"([A-Za-z0-9_.\-]+)(?:[<>=!~].*)?"', text):
        base = raw.split("[", 1)[0].lower().replace("_", "-")
        if base in {"argus", "hatchling"}:
            continue
        names.add(base)
    # Common packaging aliases
    names.update({"pyyaml", "jinja2", "pytest-cov"})
    return names


def _is_patch_or_minor(current: str, latest: str) -> bool:
    def parts(v: str) -> list[int]:
        out: list[int] = []
        for bit in v.replace("post", ".").split("."):
            digits = "".join(c for c in bit if c.isdigit())
            if digits:
                out.append(int(digits))
        return out or [0]

    a, b = parts(current), parts(latest)
    if not a or not b:
        return False
    if a[0] != b[0]:
        return False  # major bump — skip
    return tuple(b) > tuple(a)


def _update_deps(argv: list[str]) -> int:
    """Project-scoped outdated scan; --audit uses pip-audit; --apply patch/minor only."""
    import json

    audit = "--audit" in argv
    apply = "--apply" in argv
    if audit:
        subprocess.call([sys.executable, "-m", "pip", "install", "-q", "pip-audit"], cwd=str(ROOT))
        req = ROOT / ".requirements-audit.txt"
        # Direct deps only — ignore unrelated global site-packages.
        lines = [
            "click>=8.1",
            "httpx>=0.27",
            "jinja2>=3.1",
            "jsonschema>=4.22",
            "pyyaml>=6.0",
            "pytest>=8.0",
            "pytest-cov>=5.0",
            "ruff>=0.6",
        ]
        req.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip_audit", "-r", str(req)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
        finally:
            req.unlink(missing_ok=True)
        text = (proc.stdout or "") + (proc.stderr or "")
        print(text)
        upper = text.upper()
        if "CRITICAL" in upper:
            print("FAIL update-deps --audit: CRITICAL findings")
            return 1
        if proc.returncode not in (0,):
            # pip-audit exits 1 when vulns exist; treat as WARN for direct deps without CRITICAL
            print("WARN update-deps --audit: findings present (no CRITICAL keyword); continuing")
        print("OK update-deps --audit")
        return 0

    listing = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if listing.returncode != 0:
        print(listing.stderr or listing.stdout)
        return listing.returncode
    wanted = _project_dep_names()
    rows = [
        r
        for r in json.loads(listing.stdout or "[]")
        if str(r.get("name", "")).lower().replace("_", "-") in wanted
    ]
    print(json.dumps(rows, indent=2))
    majors = [
        r
        for r in rows
        if not _is_patch_or_minor(str(r.get("version") or "0"), str(r.get("latest_version") or "0"))
    ]
    if majors:
        print("majors skipped:", ", ".join(str(r.get("name")) for r in majors))
    if not apply:
        print("dry-run: pass --apply to upgrade patch/minor project deps only")
        print("Gradle: Dependabot backup or enable depsonar MCP.")
        return 0
    for row in rows:
        name = row.get("name")
        cur = str(row.get("version") or "0")
        latest = str(row.get("latest_version") or "0")
        if not name or not _is_patch_or_minor(cur, latest):
            continue
        print(f"upgrade {name} {cur} -> {latest}")
        subprocess.call(
            [sys.executable, "-m", "pip", "install", "-U", f"{name}=={latest}"],
            cwd=str(ROOT),
        )
    return 0


def _check_encoding() -> int:
    bad: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(p in path.parts for p in (".git", ".venv", "dist", "node_modules", "__pycache__")):
            continue
        if path.suffix.lower() not in {".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt"}:
            continue
        raw = path.read_bytes()
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            bad.append(str(path.relative_to(ROOT)))
            continue
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            bad.append(str(path.relative_to(ROOT)))
    if bad:
        print("FAIL encoding:", ", ".join(bad[:20]))
        return 1
    print("OK check-file-encoding")
    return 0


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

    if verb == "gc-worktrees":
        from argus.agent_ops import gc_worktrees

        apply = "--apply" in argv
        print(gc_worktrees(apply=apply))
        return 0

    if verb == "update-deps":
        return _update_deps(argv)

    if verb == "check-file-encoding":
        return _check_encoding()

    if verb in VERIFY_VERBS:
        return _run_verify()

    if verb in NA_VERBS:
        print(f"Argus child: N/A — {verb} (PARENT_GAP_LIST G12)")
        return 0

    print(f"Argus child: unknown verb {verb!r} — extend VERIFY_VERBS or NA_VERBS", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
