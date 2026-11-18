#!/usr/bin/env python3
"""sessionStart: Argus product one-liner + next AGENT row. Fail-open."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _product_snip() -> str:
    agent = ROOT / "AGENT.md"
    if agent.is_file():
        try:
            for line in agent.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#"):
                    return line.lstrip("# ").strip()[:60]
        except OSError:
            pass
    return "Argus"


def _next_agent_snip() -> str:
    path = ROOT / "BUILD_PLAN.md"
    if not path.is_file():
        return ""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if "🔲" not in line or "[AGENT]" not in line:
                continue
            if "[AGENT][LOCAL]" in line or "[AGENT]" in line:
                return stripped[:80]
    except OSError:
        return ""
    return ""


def main() -> None:
    parts = [f"product={_product_snip()}", "stack=python", "tier=foss"]
    next_agent = _next_agent_snip()
    if next_agent:
        parts.append(f"next_agent={next_agent}")
    else:
        parts.append("next_agent=board_clear type /coach")
    parts.append("gates=python scripts/agent-run.py verify")
    print(json.dumps({"user_message": "Session context: " + ", ".join(parts)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Fail-open: never block session start
        sys.exit(0)
