"""Pack paste-ready Grok Bot bootstrap prompts (no xAI create API — chat paste)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from argus.paths import DIST_DIR, ROOT, ensure_runtime_dirs

STEWARD_ID = "tuesday-steward"
SKILL_REL = Path("docs/grok-bots/09-tuesday-steward.md")
PREAMBLE_REL = Path("docs/grok-bots/00-shared-preamble.md")


def _read(rel: Path) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def pack_tuesday_steward(*, allowlist: list[str] | None = None) -> dict[str, Any]:
    """Write dist/grok-bots/tuesday-steward-bootstrap.md for one-paste Bot setup."""
    ensure_runtime_dirs()
    out_dir = DIST_DIR / "grok-bots"
    out_dir.mkdir(parents=True, exist_ok=True)
    allow = allowlist or ["edwardlthompson/Argus"]
    allow_txt = ", ".join(f"`{a}`" for a in allow)
    preamble = _read(PREAMBLE_REL).strip()
    skill = _read(SKILL_REL).strip()
    body = f"""# Tuesday Steward — paste into Grok Bot chat

xAI has **no public API** to create Bots. Paste this message into a new Grok Bot
(or an existing maintenance Bot) to save the skill and schedule the routine.

---

Create a Bot (or rename this one) called **Tuesday Steward**.

{preamble}

Allowlist for this Bot: {allow_txt}

Save the following as a skill named **Tuesday Steward portfolio digest**:

```
{skill}
```

Then create a routine:

> Every Tuesday at 4:00 PM America/New_York (after Monday Dependabot and the
> Argus weekly YOLO run at 14:00 UTC), run the Tuesday Steward portfolio digest
> skill. Lead with private `steward-brief.html` (or
> `argus-history/reports/latest-steward.html`). Also use `health-delta.md`,
> `health-hotspots.json`, and `health-infographic.svg`. Never publish finding
> titles to a public Page. Post a steward-digest in this chat. Never merge.
> If artifacts missing, say so and list open upgrade/chore PRs from GitHub only.

Also accept a webhook trigger named **after-argus-weekly** so Argus can POST
when the Tuesday scan finishes (optional).

Confirm the routine schedule, allowlist, and that merge is forbidden.
"""
    path = out_dir / "tuesday-steward-bootstrap.md"
    path.write_text(body + "\n", encoding="utf-8")
    return {
        "bot": "Tuesday Steward",
        "bootstrap": str(path),
        "allowlist": allow,
        "note": "Paste bootstrap into Grok Bot chat; no remote create API.",
    }
