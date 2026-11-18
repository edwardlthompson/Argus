"""Budget counters for Argus apply + Grok digests."""

from __future__ import annotations

from typing import Any

from argus.grok_budget import load_counters, load_grok_config
from argus.paths import DIST_DIR


def report() -> dict[str, Any]:
    grok_cfg = load_grok_config()
    grok = load_counters()
    actions = 0
    path = DIST_DIR / "actions.jsonl"
    if path.is_file():
        actions = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return {
        "argus_actions_logged": actions,
        "grok": {
            "day": grok.day,
            "runs": grok.runs,
            "tokens": grok.tokens,
            "errors": grok.errors,
            "caps": {
                "max_total_bot_runs_per_day": grok_cfg.get("max_total_bot_runs_per_day"),
                "max_estimated_tokens_per_day": grok_cfg.get("max_estimated_tokens_per_day"),
            },
        },
    }
