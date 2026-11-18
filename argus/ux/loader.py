"""Load stack UX rules with BASE_EXCLUDES / _SKIP."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from argus.paths import PROJECT_ROOT

BASE_EXCLUDES = frozenset({
    "*.md",
    "*.mdc",
    "*.txt",
    "LICENSE*",
    "CHANGELOG*",
    "THIRD_PARTY*",
})
SKIP_PREFIXES = (".cursor/", "examples/", "node_modules/", ".venv/", "dist/")


def _excluded(rel: str) -> bool:
    p = rel.replace("\\", "/")
    if any(p.startswith(s) for s in SKIP_PREFIXES):
        return True
    name = Path(p).name
    for pat in BASE_EXCLUDES:
        if pat.startswith("*.") and name.lower().endswith(pat[1:].lower()):
            return True
        if pat.endswith("*") and not pat.startswith("*"):
            if name.startswith(pat[:-1]):
                return True
        elif name == pat or Path(p).match(pat):
            return True
    return False


def load_rules(stack: str, rules_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load argus/ux/rules/{stack}/*.yaml — empty list if no fixtures."""
    base = rules_dir or (PROJECT_ROOT / "argus" / "ux" / "rules" / stack)
    if not base.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(base.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not data.get("id"):
            continue
        data["_path"] = str(path)
        out.append(data)
    return out


def scan_paths(root: Path, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not rules:
        return findings
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if _excluded(rel):
            continue
        text = ""
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for rule in rules:
            pat = rule.get("regex")
            if not pat:
                continue
            if re.search(str(pat), text, re.M):
                findings.append({
                    "rule_id": rule["id"],
                    "path": rel,
                    "severity": rule.get("severity", "low"),
                })
    return findings


def ensure_baseline(root: Path) -> tuple[Path, bool]:
    """Empty ux-baseline.json on fresh repo; returns (path, created)."""
    path = root / "ux-baseline.json"
    if path.is_file():
        return path, False
    path.write_text("{}\n", encoding="utf-8")
    return path, True
