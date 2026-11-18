"""Deterministic BUILD_PLAN transforms. Never invents tasks."""

from __future__ import annotations

import re
from functools import lru_cache

from argus.board_classify import NEWS_HEAD, missing_markers
from argus.config_loader import load_yaml
from argus.paths import CONFIG_DIR

_ROLE = re.compile(r"\[(AGENT|HUMAN|ADB|AUTO)\]", re.I)


@lru_cache(maxsize=1)
def stubs() -> dict[str, str]:
    data = load_yaml(CONFIG_DIR / "board_markers.yaml") or {}
    raw = data.get("markers") if isinstance(data, dict) else {}
    return {str(k): str(v).rstrip() + "\n" for k, v in (raw or {}).items()}


def _news_span(text: str) -> tuple[int, int] | None:
    match = NEWS_HEAD.search(text)
    if not match:
        return None
    rest = text[match.end() :]
    nxt = re.search(r"^#{1,6}\s+\S", rest, re.M)
    return match.start(), match.end() + (nxt.start() if nxt else len(rest))


def _ensure_bullet(line: str) -> str:
    stripped = line.strip()
    return stripped if stripped[:1] in "-*123456789" else f"- {stripped}"


def _with_local_venue(row: str) -> str:
    if re.search(r"\[AGENT\]", row, re.I) and not re.search(r"\[(LOCAL|CLOUD)\]", row):
        return re.sub(r"\[AGENT\]", "[AGENT][LOCAL]", row, count=1, flags=re.I)
    return row


def split_open_rows(text: str) -> tuple[list[str], list[str]]:
    agent: list[str] = []
    human: list[str] = []
    for line in (text or "").splitlines():
        if "🔲" not in line and "❌" not in line and "[ ]" not in line:
            continue
        role_m = _ROLE.search(line)
        role = role_m.group(1).upper() if role_m else "AGENT"
        row = _ensure_bullet(line)
        (human if role in ("HUMAN", "ADB") else agent).append(
            row if role in ("HUMAN", "ADB") else _with_local_venue(row)
        )
    return agent, human


def _insert_lane_rows(text: str, marker: str, rows: list[str]) -> str:
    if not rows:
        return text
    begin, end = f"<!-- {marker}:begin -->", f"<!-- {marker}:end -->"
    if begin not in text:
        return text
    i = text.index(begin) + len(begin)
    j = text.find(end, i)
    if j < 0:
        return text
    body = text[i:j]
    for placeholder in ("_No local agent items._", "_No cloud agent items._"):
        body = body.replace(placeholder, "")
    merged = "\n" + "\n".join(x for x in (body.strip(), "\n".join(rows)) if x) + "\n"
    return text[:i] + merged + text[j:]


def fold_news_inbox(text: str) -> str:
    span = _news_span(text)
    if not span:
        return text
    start, end = span
    agent, human = split_open_rows(text[start:end])
    out = _insert_lane_rows(text[:start].rstrip() + "\n" + text[end:].lstrip("\n"), "local-agent-lane", agent)
    if not human:
        return out
    if "### Waiting on a person" in out:
        return out.replace("### Waiting on a person", "### Waiting on a person\n\n" + "\n".join(human), 1)
    return out.rstrip() + "\n\n### Waiting on a person\n\n" + "\n".join(human) + "\n"


def append_missing_markers(text: str) -> str:
    """Partial-board auto_safe: stubs for missing markers, then fold News inbox."""
    out = text or ""
    missing = missing_markers(out)
    blocks = stubs()
    if "remaining-tally" in missing:
        tally = blocks["remaining-tally"]
        heading = re.search(r"^# .+$", out, re.M)
        out = (out[: heading.end()] + "\n\n" + tally + out[heading.end() :]) if heading else tally + "\n" + out
    rest = [blocks[m] for m in missing if m != "remaining-tally" and m in blocks]
    if rest:
        out = out.rstrip() + "\n\n" + "\n".join(rest) + "\n"
    return fold_news_inbox(out)


def restructure_divergent(text: str, *, source_path: str, has_completed_tasks: bool) -> dict[str, str]:
    """APB skeleton plus extracted open rows. Original quoted so nothing is lost."""
    agent, human = split_open_rows(text or "")
    blocks = stubs()
    lane = blocks["local-agent-lane"].replace(
        "_No local agent items._", "\n".join(agent) if agent else "_No local agent items._"
    )
    human_block = "### Waiting on a person\n\n" + "\n".join(human) + "\n\n" if human else ""
    hist = (
        "Finished work: [`COMPLETED_TASKS.md`](COMPLETED_TASKS.md).\n"
        if has_completed_tasks
        else "Completed history is quoted in Preserved source board below.\n"
    )
    archive = "Older sprints: [`COMPLETED_TASKS.md`](COMPLETED_TASKS.md).\n\n" if has_completed_tasks else ""
    root = (
        "# Build Plan\n\n"
        f"{blocks['remaining-tally']}\nLive board. Canonical shape: agent-project-bootstrap "
        f"`BUILD_PLAN_TEMPLATE.md`.\n{hist}\n"
        "**Who:** `AGENT` code · `HUMAN` person · `ADB` device · `AUTO` CI/scripts\n"
        "**Venue (AGENT only):** `[LOCAL]` This Computer · `[CLOUD]` Cursor Cloud\n"
        "**State:** 🔲 open · ✅ done · ❌ blocked\n\n"
        "Format: `🔲 [AGENT][LOCAL] Short task — scope: path/prefix`.\n\n"
        f"{blocks['open-prs-sync']}\n{blocks['template-gaps-sync']}\n{human_block}{lane}\n"
        f"{blocks['cloud-agent-lane']}\n## Archive\n\n{archive}"
        "## Preserved source board\n\nQuoted so no prior task is lost. Prefer the lanes above; "
        "do not invent work.\n\n<details>\n<summary>Previous board</summary>\n\n"
        + (text or "").rstrip()
        + "\n\n</details>\n"
    )
    files = {"BUILD_PLAN.md": root}
    if source_path.replace("\\", "/").endswith("docs/BUILD_PLAN.md"):
        files["docs/BUILD_PLAN.md"] = (
            "# BUILD_PLAN moved\n\nThe live board is [`/BUILD_PLAN.md`](../BUILD_PLAN.md).\n"
        )
    return files
