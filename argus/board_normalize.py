"""Deterministic BUILD_PLAN transforms. Never invents tasks."""

from __future__ import annotations

import re
from functools import lru_cache

from argus.board_classify import NEWS_HEAD, missing_markers
from argus.board_queue import (
    ParserCaps,
    default_caps,
    ensure_queue_visible,
    format_agent_line,
    insert_before_stop,
    insert_lane_rows,
    preserve_source,
)
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


def _render_stub(block: str, caps: ParserCaps) -> str:
    if caps.venue:
        return block
    return block.replace("[AGENT][LOCAL]", "[AGENT]").replace("[AGENT][CLOUD]", "[AGENT]")


def _outside_code(line: str) -> str:
    return re.sub(r"`[^`]*`", "", line)


def _as_row(line: str) -> str:
    stripped = line.strip()
    if stripped[:1] in "-*" or re.match(r"^\d", stripped):
        return stripped
    return f"- {stripped}"


def split_open_rows(text: str, *, caps: ParserCaps | None = None) -> tuple[list[str], list[str]]:
    caps = caps or default_caps()
    agent: list[str] = []
    human: list[str] = []
    for line in (text or "").splitlines():
        visible = _outside_code(line)
        if "🔲" not in visible and "❌" not in visible and "[ ]" not in visible:
            continue
        if line.lstrip().startswith(">"):
            continue
        role_m = _ROLE.search(visible)
        role = role_m.group(1).upper() if role_m else "AGENT"
        if role in ("HUMAN", "ADB"):
            human.append(_as_row(line))
        else:
            agent.append(format_agent_line(line, caps))
    return agent, human


def fold_news_inbox(text: str, *, caps: ParserCaps | None = None) -> str:
    caps = caps or default_caps()
    span = _news_span(text)
    if not span:
        return text
    start, end = span
    agent, human = split_open_rows(text[start:end], caps=caps)
    kept = text[:start].rstrip() + "\n" + text[end:].lstrip("\n")
    out = insert_lane_rows(kept, "local-agent-lane", agent)
    if not human:
        return out
    if "### Waiting on a person" in out:
        return out.replace("### Waiting on a person", "### Waiting on a person\n\n" + "\n".join(human), 1)
    return out.rstrip() + "\n\n### Waiting on a person\n\n" + "\n".join(human) + "\n"


def append_missing_markers(text: str, *, caps: ParserCaps | None = None) -> str:
    """Partial-board auto_safe: stubs for missing markers, then fold News inbox.

    Lane stubs go before the child's first stop heading (``## Archive`` /
    ``## Ongoing Maintenance``, including ``## Archived Sprints``). Rows are
    shaped for that parser, then ``ensure_queue_visible`` repairs anything
    still below the stop or trapped by a preserved-board quote.
    """
    caps = caps or default_caps()
    out = text or ""
    missing = missing_markers(out)
    blocks = stubs()
    if "remaining-tally" in missing:
        tally = blocks["remaining-tally"]
        heading = re.search(r"^# .+$", out, re.M)
        out = (out[: heading.end()] + "\n\n" + tally + out[heading.end() :]) if heading else tally + "\n" + out
    rest = [_render_stub(blocks[m], caps) for m in missing if m != "remaining-tally" and m in blocks]
    if rest:
        out = insert_before_stop(out, "\n".join(rest), caps)
    return ensure_queue_visible(fold_news_inbox(out, caps=caps), caps)


def restructure_divergent(
    text: str,
    *,
    source_path: str,
    has_completed_tasks: bool,
    caps: ParserCaps | None = None,
) -> dict[str, str]:
    """APB skeleton plus extracted open rows. Original quoted so nothing is lost."""
    caps = caps or default_caps()
    agent, human = split_open_rows(text or "", caps=caps)
    blocks = stubs()
    lane = _render_stub(blocks["local-agent-lane"], caps).replace(
        "_No local agent items._", "\n".join(agent) if agent else "_No local agent items._"
    )
    cloud = _render_stub(blocks["cloud-agent-lane"], caps)
    human_block = "### Waiting on a person\n\n" + "\n".join(human) + "\n\n" if human else ""
    hist = (
        "Finished work: [`COMPLETED_TASKS.md`](COMPLETED_TASKS.md).\n"
        if has_completed_tasks
        else "Completed history is quoted in Preserved source board below.\n"
    )
    archive = "Older sprints: [`COMPLETED_TASKS.md`](COMPLETED_TASKS.md).\n\n" if has_completed_tasks else ""
    quoted = preserve_source(text or "", caps)
    row_fmt = "[AGENT][LOCAL]" if caps.venue else "[AGENT]"
    root = (
        "# Build Plan\n\n"
        f"{blocks['remaining-tally']}\nLive board. Canonical shape: agent-project-bootstrap "
        f"`BUILD_PLAN_TEMPLATE.md`.\n{hist}\n"
        "**Who:** `AGENT` code · `HUMAN` person · `ADB` device · `AUTO` CI/scripts\n"
        "**Venue (AGENT only):** `[LOCAL]` This Computer · `[CLOUD]` Cursor Cloud\n"
        "**State:** 🔲 open · ✅ done · ❌ blocked\n\n"
        f"Format: `🔲 {row_fmt} Short task — scope: path/prefix`.\n\n"
        f"{blocks['open-prs-sync']}\n{blocks['template-gaps-sync']}\n{human_block}{lane}\n"
        f"{cloud}\n## Archive\n\n{archive}"
        "## Preserved source board\n\nQuoted so no prior task is lost. Prefer the lanes above; "
        "do not invent work.\n\n"
        + quoted
    )
    root = ensure_queue_visible(root, caps)
    files = {"BUILD_PLAN.md": root}
    if source_path.replace("\\", "/").endswith("docs/BUILD_PLAN.md"):
        files["docs/BUILD_PLAN.md"] = (
            "# BUILD_PLAN moved\n\nThe live board is [`/BUILD_PLAN.md`](../BUILD_PLAN.md).\n"
        )
    return files
