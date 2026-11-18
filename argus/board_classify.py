"""Classify BUILD_PLAN.md against APB marker lanes. Pure."""

from __future__ import annotations

import re
from typing import Any

BOARD_MARKERS = (
    "remaining-tally",
    "local-agent-lane",
    "cloud-agent-lane",
    "open-prs-sync",
    "template-gaps-sync",
)
APB_HINTS = BOARD_MARKERS + (
    "[LOCAL]",
    "[CLOUD]",
    "Open PRs (synced)",
    "Template gaps (synced)",
    "Local agent (This Computer)",
)
NEWS_HEAD = re.compile(r"^#{1,3}\s+News inbox \(synced\)\s*$", re.I | re.M)


def locate_board_path(*, root_exists: bool, docs_exists: bool) -> str | None:
    if root_exists:
        return "BUILD_PLAN.md"
    if docs_exists:
        return "docs/BUILD_PLAN.md"
    return None


def missing_markers(text: str) -> list[str]:
    return [m for m in BOARD_MARKERS if m not in (text or "")]


def looks_apb(text: str) -> bool:
    return any(hint in (text or "") for hint in APB_HINTS)


def classify_board(text: str | None, path: str | None) -> dict[str, Any]:
    if not path or text is None:
        return {
            "kind": "missing",
            "path": path,
            "missing_markers": list(BOARD_MARKERS),
            "has_news_inbox": False,
            "docs_only": False,
            "looks_apb": False,
        }
    news = bool(NEWS_HEAD.search(text))
    missing = missing_markers(text)
    apb = looks_apb(text)
    docs_only = path.replace("\\", "/").endswith("docs/BUILD_PLAN.md")
    if apb and not missing and not news:
        kind = "canonical"
    elif apb:
        kind = "partial"
    else:
        kind = "divergent"
    return {
        "kind": kind,
        "path": path,
        "missing_markers": missing,
        "has_news_inbox": news,
        "docs_only": docs_only,
        "looks_apb": apb,
    }
