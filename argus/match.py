"""Match fixes against signal context using applies_when expressions."""

from __future__ import annotations

from typing import Any

from argus.expr import ExprError, evaluate
from argus.models import Fix, MatchedFix, RepoRecord, SignalBundle
from argus.state import StateStore


def build_context(repo: RepoRecord, signals: SignalBundle) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "repo": {
            "full_name": repo.full_name,
            "status": repo.status.value,
            "private": repo.private,
            "archived": repo.archived,
            "fork": repo.fork,
            "can_write": repo.can_write,
            "description": repo.description or "",
            "topics": list(repo.topics),
        },
        "signals": signals.as_dict(),
    }
    # Flatten categories for convenience in expressions
    for cat, data in signals.as_dict().items():
        ctx[cat] = data or {}
    return ctx


def match_fixes(
    fixes: list[Fix],
    repo: RepoRecord,
    signals: SignalBundle,
    store: StateStore | None,
    *,
    profile: str = "generic",
) -> list[MatchedFix]:
    ctx = build_context(repo, signals)
    matched: list[MatchedFix] = []
    for fix in fixes:
        if profile not in fix.profiles and "generic" not in fix.profiles:
            continue
        if store and store.is_resolved(repo.full_name, fix.id):
            continue
        try:
            if evaluate(fix.applies_when, ctx):
                matched.append(MatchedFix(fix=fix, reason=fix.applies_when))
        except ExprError:
            # Bad expression → skip rather than crash a whole run
            continue
    return matched
