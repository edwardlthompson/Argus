"""UX rule loader — native linter first, regex fallback. No fixtures ⇒ rule does not load."""

from __future__ import annotations

from argus.ux.loader import BASE_EXCLUDES, SKIP_PREFIXES, load_rules, scan_paths
from argus.ux.rollout import actionable, reportable, stage_for

__all__ = [
    "BASE_EXCLUDES",
    "SKIP_PREFIXES",
    "actionable",
    "load_rules",
    "reportable",
    "scan_paths",
    "stage_for",
]
