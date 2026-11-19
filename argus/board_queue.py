"""Child /build queue compatibility. Mirrors vendored APB parsers; does not import them."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_OPEN = r"(?:🔲|⬜|\[ \])"
_OWNER = r"(?:AGENT|AUTO|HUMAN|ADB)"
_AGENT_OWNER = r"(?:AGENT|AUTO)"
_CANDIDATE = re.compile(
    rf"^(?:[-*] |\d+[a-z]?\.\s+){_OPEN}\s+\[(?P<owner>{_AGENT_OWNER})\]"
    rf"(?:\[(?P<venue>LOCAL|CLOUD)\])?\s+(?P<task>.+)$"
)
_SPRINT = re.compile(r"^###\s+Sprint\s+", re.I)
_PARALLEL = re.compile(r"^#{3,4}\s+.*Parallel", re.I)
_SEQUENTIAL = re.compile(r"^#{3,4}\s+.*Sequential", re.I)
_HUMAN = re.compile(r"^#{3,4}\s+.*Human.*after automation", re.I)
_DEFAULT_TRIGGERS = ("## Child Repo Playbook", "#### Sequential")
_DEFAULT_STOPS = ("## Archive", "## Ongoing Maintenance")
_LANES = (
    ("local-agent-lane", "### Local agent"),
    ("cloud-agent-lane", "### Cloud agent"),
)


@dataclass(frozen=True)
class ParserCaps:
    """What a child's vendored build_sprint*.py will actually read."""

    venue: bool = True
    legacy_triggers: tuple[str, ...] = _DEFAULT_TRIGGERS
    stop_prefixes: tuple[str, ...] = _DEFAULT_STOPS
    has_slim: bool = True
    has_legacy: bool = True


def default_caps() -> ParserCaps:
    return ParserCaps()


def caps_from_sources(
    *,
    model: str | None,
    child: str | None,
    parse: str | None,
    sprint: str | None = None,
) -> ParserCaps:
    """Detect venue, slim vs legacy, and stop headings from vendored parser source.

    ``parse_numbered_board`` lives in ``build_sprint_parse.py`` on current APB and in
    ``build_sprint_child.py`` on some drifted copies. Legacy-only drivers call
    ``parse_sprint_blocks`` and never read lane bullets.
    """
    blobs = [blob for blob in (model, child, parse, sprint) if blob]
    if not blobs:
        return default_caps()
    venue = _venue_supported(model) if model else True
    triggers = _legacy_triggers(blobs)
    joined = "\n".join(blobs)
    has_slim = "def parse_numbered_board" in joined or "def parse_board_queue" in joined
    has_legacy = bool(triggers) or "def uses_legacy_playbook" in joined
    if not has_slim and ("def parse_sprint_blocks" in joined or "parse_sprint_blocks(" in joined):
        has_legacy = True
    return ParserCaps(
        venue=venue,
        legacy_triggers=triggers,
        stop_prefixes=_stop_prefixes(blobs),
        has_slim=has_slim,
        has_legacy=has_legacy,
    )


def caps_from_root(root: Path) -> ParserCaps:
    def read(rel: str) -> str | None:
        path = root / rel
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    return caps_from_sources(
        model=read("scripts/lib/build_sprint_model.py"),
        child=read("scripts/lib/build_sprint_child.py"),
        parse=read("scripts/lib/build_sprint_parse.py"),
        sprint=read("scripts/lib/build_sprint.py"),
    )


def _venue_supported(model: str) -> bool:
    if re.search(r"LOCAL\|CLOUD", model):
        return True
    if "ROW_BULLET" in model or "ROW_NUMBERED" in model:
        return False
    return True


def _legacy_triggers(blobs: list[str]) -> tuple[str, ...]:
    for blob in blobs:
        fn = re.search(r"def uses_legacy_playbook\b.*?(?=\ndef |\Z)", blob, re.S)
        if not fn:
            continue
        found = tuple(dict.fromkeys(re.findall(r'"([^"]+)"', fn.group(0))))
        return found or _DEFAULT_TRIGGERS
    return ()


def _stop_prefixes(blobs: list[str]) -> tuple[str, ...]:
    """Stop headings inside ``parse_numbered_board`` only.

    Other helpers call ``startswith("## ")`` and ``startswith("## Child Repo Playbook")``.
    Those are not the slim-queue break.
    """
    found: list[str] = []
    saw_fn = False
    for blob in blobs:
        fn = re.search(r"def parse_numbered_board\b.*?(?=\ndef |\Z)", blob, re.S)
        if not fn:
            continue
        saw_fn = True
        for item in re.findall(r"""startswith\(\s*["']([^"']+)["']\s*\)""", fn.group(0)):
            if not re.match(r"^##\s+\S", item) or item.startswith("###"):
                continue
            if "Template Maintainer" in item or "Child Repo Playbook" in item:
                continue
            if item not in found:
                found.append(item)
    if found:
        return tuple(found)
    return () if saw_fn else _DEFAULT_STOPS


def legacy_active(text: str, caps: ParserCaps) -> bool:
    if not caps.has_legacy:
        return False
    return any(trigger in (text or "") for trigger in caps.legacy_triggers)


def first_stop_offset(text: str, caps: ParserCaps) -> int | None:
    offset = 0
    for line in (text or "").splitlines(keepends=True):
        if any(line.startswith(prefix) for prefix in caps.stop_prefixes):
            return offset
        offset += len(line)
    return None


def format_agent_line(row: str, caps: ParserCaps) -> str:
    """Bullet or numbered open row the child's row regex can match."""
    line = row.strip()
    line = re.sub(r"^\*\s+", "- ", line)
    if not re.match(r"^(?:- |\d+[a-z]?\.\s+)", line):
        line = f"- {line}"
    if caps.venue:
        if re.search(r"\[AGENT\]", line, re.I) and not re.search(r"\[(?:LOCAL|CLOUD)\]", line):
            line = re.sub(r"\[AGENT\]", "[AGENT][LOCAL]", line, count=1, flags=re.I)
        return line
    line = re.sub(r"\[(AGENT|AUTO)\]\[(?:LOCAL|CLOUD)\]", r"[\1]", line, count=1, flags=re.I)
    return re.sub(r"\[(AGENT|AUTO)\](?!\s)", r"[\1] ", line, count=1, flags=re.I)


def break_triggers(text: str, caps: ParserCaps) -> str:
    for trigger in caps.legacy_triggers:
        if trigger not in text:
            continue
        if " " in trigger:
            replacement = trigger.replace(" ", " · ", 1)
        else:
            mid = max(1, len(trigger) // 2)
            replacement = trigger[:mid] + "·" + trigger[mid:]
        text = text.replace(trigger, replacement)
    return text


def child_picks(text: str, caps: ParserCaps | None = None) -> list[str]:
    """Open AGENT/AUTO task texts the child's /build queue would see, in order."""
    caps = caps or default_caps()
    body = text or ""
    if not caps.has_slim or (caps.has_legacy and legacy_active(body, caps)):
        return _legacy_tasks(body, caps)
    return _slim_tasks(body, caps)


def invisible_open_rows(text: str, caps: ParserCaps | None = None) -> list[str]:
    """Open agent rows (and preserved-board legacy traps) the child parser will not return."""
    caps = caps or default_caps()
    body = text or ""
    if not body:
        return []
    picked = set(child_picks(body, caps))
    masked = re.sub(r"<details>.*?</details>", "", body, flags=re.S)
    missing: list[str] = []
    for line in masked.splitlines():
        if line.lstrip().startswith(">"):
            continue
        match = _CANDIDATE.match(line.strip())
        if match and match.group("task").strip() not in picked:
            missing.append(line.strip())
    if _preserved_shadows_queue(body, caps):
        missing.append("preserved board text trips legacy /build mode")
    return missing


def ensure_queue_visible(text: str, caps: ParserCaps | None = None) -> str:
    """Move and rewrite open agent rows so this child's parser returns them."""
    caps = caps or default_caps()
    original = text or ""
    out = _relocate_after_stop(original, caps)
    out = _neutralize_details(out, caps)
    out = _break_triggers_after_stop(out, caps)
    out = _break_stray_live_triggers(out, caps)
    out = _promote_after_stop(out, caps)
    if not caps.has_slim:
        out = _ensure_playbook(out, caps)
        out = _lift_unpicked(out, caps)
    elif legacy_active(out, caps) and "## Child Repo Playbook" in _live_region(out, caps):
        out = _lift_unpicked(out, caps)
    out = _adapt_unpicked(out, caps)
    if out == original:
        return original
    return out if out.endswith("\n") else out + "\n"


def insert_before_stop(text: str, block: str, caps: ParserCaps) -> str:
    blob = block.strip()
    if not blob:
        return text
    stop = first_stop_offset(text, caps)
    piece = blob + "\n\n"
    if stop is None:
        return text.rstrip() + "\n\n" + piece
    return text[:stop].rstrip() + "\n\n" + piece + text[stop:]


def insert_lane_rows(text: str, marker: str, rows: list[str]) -> str:
    if not rows:
        return text
    begin, end = f"<!-- {marker}:begin -->", f"<!-- {marker}:end -->"
    if begin not in text:
        return text
    start = text.index(begin) + len(begin)
    stop = text.find(end, start)
    if stop < 0:
        return text
    body = text[start:stop]
    for placeholder in ("_No local agent items._", "_No cloud agent items._"):
        body = body.replace(placeholder, "")
    merged = "\n" + "\n".join(part for part in (body.strip(), "\n".join(rows)) if part) + "\n"
    return text[:start] + merged + text[stop:]


def preserve_source(text: str, caps: ParserCaps) -> str:
    raw = "<details>\n<summary>Previous board</summary>\n\n" + (text or "").rstrip() + "\n</details>\n"
    return _neutralize_details(raw, caps)


def _row_regex(caps: ParserCaps, *, numbered_only: bool) -> re.Pattern[str]:
    venue = r"(?:\[(?:LOCAL|CLOUD)\])?" if caps.venue else ""
    prefix = r"(?P<num>\d+[a-z]?)\.\s+" if numbered_only else r"(?:(?P<num>\d+[a-z]?)\.\s+|-\s)"
    return re.compile(
        rf"^{prefix}{_OPEN}\s+\[(?P<owner>{_OWNER})\]{venue}\s+(?P<task>.+)$"
    )


def _slim_tasks(text: str, caps: ParserCaps) -> list[str]:
    regex = _row_regex(caps, numbered_only=False)
    tasks: list[str] = []
    for line in text.splitlines():
        if any(line.startswith(prefix) for prefix in caps.stop_prefixes):
            break
        match = regex.match(line)
        if match and match.group("owner") in ("AGENT", "AUTO"):
            tasks.append(match.group("task").strip())
    seen = set(tasks)
    for task in _maintenance_tasks(text, caps):
        if task not in seen:
            tasks.append(task)
            seen.add(task)
    return tasks


def _maintenance_tasks(text: str, caps: ParserCaps) -> list[str]:
    """Bullets under ``## Ongoing Maintenance`` are a second queue, even past Archive."""
    regex = _row_regex(caps, numbered_only=False)
    tasks: list[str] = []
    in_maint = False
    for line in text.splitlines():
        if line.startswith("## Ongoing Maintenance"):
            in_maint = True
            continue
        if not in_maint:
            continue
        if line.startswith("## ") and not line.startswith("### "):
            break
        if not line.startswith("- "):
            continue
        match = regex.match(line)
        if match and match.group("owner") in ("AGENT", "AUTO"):
            tasks.append(match.group("task").strip())
    return tasks


def _legacy_tasks(text: str, caps: ParserCaps) -> list[str]:
    lines = text.splitlines()
    regex = _row_regex(caps, numbered_only=True)
    tasks: list[str] = []
    in_child = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith("## Child Repo Playbook"):
            in_child = True
            index += 1
            continue
        if not in_child:
            index += 1
            continue
        if line.startswith("## Ongoing Maintenance"):
            break
        if _SPRINT.match(line):
            block = [line]
            index += 1
            while index < len(lines) and not (
                _SPRINT.match(lines[index])
                or (lines[index].startswith("## ") and not lines[index].startswith("### "))
            ):
                block.append(lines[index])
                index += 1
            tasks.extend(_tasks_in_sprint(block, regex))
            continue
        index += 1
    return tasks


def _tasks_in_sprint(block: list[str], regex: re.Pattern[str]) -> list[str]:
    phase = "pre"
    tasks: list[str] = []
    for line in block:
        if line.startswith("### Sprint") or line.startswith("<!--"):
            continue
        if _PARALLEL.match(line):
            phase = "parallel"
            continue
        if _HUMAN.match(line):
            phase = "human"
            continue
        if phase == "parallel" and _SEQUENTIAL.match(line):
            phase = "post"
            continue
        if phase == "parallel":
            continue
        match = regex.match(line)
        if match and match.group("owner") in ("AGENT", "AUTO"):
            tasks.append(match.group("task").strip())
    return tasks


def _live_region(text: str, caps: ParserCaps) -> str:
    stripped = re.sub(r"<details>.*?</details>", "", text, flags=re.S)
    stop = first_stop_offset(stripped, caps)
    return stripped if stop is None else stripped[:stop]


def _preserved_shadows_queue(text: str, caps: ParserCaps) -> bool:
    live = _live_region(text, caps)
    if not caps.has_slim:
        return "## Child Repo Playbook" in text and "## Child Repo Playbook" not in live
    if not legacy_active(text, caps):
        return False
    return not legacy_active(live, caps)


def _lane_span(text: str, marker: str, heading: str) -> tuple[int, int] | None:
    begin = text.find(f"<!-- {marker}:begin -->")
    end_tag = f"<!-- {marker}:end -->"
    end = text.find(end_tag)
    if begin < 0 or end < begin:
        return None
    end_pos = end + len(end_tag)
    if end_pos < len(text) and text[end_pos] == "\n":
        end_pos += 1
    start = begin
    head = text.rfind(heading, 0, begin)
    if head >= 0:
        line_start = text.rfind("\n", 0, head) + 1
        between = text[line_start:begin]
        if "\n## " not in "\n" + between and "\n### " not in between[len(heading) :]:
            start = line_start
    return start, end_pos


def _section_span(text: str, heading: str) -> tuple[int, int] | None:
    line_at = 0
    start: int | None = None
    for line in text.splitlines(keepends=True):
        if start is None and line.startswith(heading):
            start = line_at
        elif start is not None and (line.startswith("## ") or line.startswith("### ")):
            return start, line_at
        line_at += len(line)
    if start is None:
        return None
    return start, len(text)


def _relocate_after_stop(text: str, caps: ParserCaps) -> str:
    stop = first_stop_offset(text, caps)
    if stop is None:
        return text
    spans: list[tuple[int, int]] = []
    for marker, heading in _LANES:
        span = _lane_span(text, marker, heading)
        if span and span[0] >= stop:
            spans.append(span)
    waiting = _section_span(text, "### Waiting on a person")
    if waiting and waiting[0] >= stop:
        spans.append(waiting)
    if not spans:
        return text
    spans.sort()
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    blocks: list[str] = []
    parts: list[str] = []
    cursor = 0
    for start, end in merged:
        parts.append(text[cursor:start])
        blocks.append(text[start:end].strip("\n"))
        cursor = end
    parts.append(text[cursor:])
    body = "".join(parts)
    stop2 = first_stop_offset(body, caps)
    blob = "\n\n".join(blocks).strip() + "\n\n"
    if stop2 is None:
        return body.rstrip() + "\n\n" + blob
    return body[:stop2].rstrip() + "\n\n" + blob + body[stop2:]


def _neutralize_details(text: str, caps: ParserCaps) -> str:
    if "<details>" not in text:
        return text

    def repl(match: re.Match[str]) -> str:
        lines: list[str] = []
        for line in break_triggers(match.group(1), caps).splitlines():
            if "<summary>" in line or "</summary>" in line or not line.strip() or line.startswith(">"):
                lines.append(line)
            else:
                lines.append("> " + line)
        return "<details>\n" + "\n".join(lines).strip("\n") + "\n</details>"

    return re.sub(r"<details>(.*?)</details>", repl, text, flags=re.S)


def _break_triggers_after_stop(text: str, caps: ParserCaps) -> str:
    stop = first_stop_offset(text, caps)
    if stop is None or not any(trigger in text[stop:] for trigger in caps.legacy_triggers):
        return text
    return text[:stop] + break_triggers(text[stop:], caps)


def _break_stray_live_triggers(text: str, caps: ParserCaps) -> str:
    live = _live_region(text, caps)
    if not legacy_active(live, caps) or "## Child Repo Playbook" in live:
        return text
    out: list[str] = []
    in_details = False
    stopped = False
    changed = False
    for line in text.splitlines():
        if "<details>" in line:
            in_details = True
        is_stop = any(line.startswith(prefix) for prefix in caps.stop_prefixes)
        if not stopped and not in_details and not is_stop:
            broken = break_triggers(line, caps)
            changed = changed or broken != line
            line = broken
        if is_stop and not in_details:
            stopped = True
        out.append(line)
        if "</details>" in line:
            in_details = False
    if not changed:
        return text
    rejoined = "\n".join(out)
    return rejoined + ("\n" if text.endswith("\n") else "")


def _promote_after_stop(text: str, caps: ParserCaps) -> str:
    stop = first_stop_offset(text, caps)
    if stop is None:
        return text
    head, tail = text[:stop], text[stop:]
    kept: list[str] = []
    moved: list[str] = []
    in_details = False
    in_maint = False
    # Slim mode reads the maintenance section on purpose. Legacy mode does not.
    honor_maint = caps.has_slim and not legacy_active(text, caps)
    for line in tail.splitlines():
        if "<details>" in line:
            in_details = True
        if line.startswith("## Ongoing Maintenance"):
            in_maint = True
        elif in_maint and line.startswith("## ") and not line.startswith("### "):
            in_maint = False
        if (
            not in_details
            and not (honor_maint and in_maint)
            and not line.lstrip().startswith(">")
            and _CANDIDATE.match(line.strip())
        ):
            moved.append(line.strip())
        else:
            kept.append(line)
        if "</details>" in line:
            in_details = False
    if not moved:
        return text
    new_tail = "\n".join(kept)
    if tail.endswith("\n"):
        new_tail += "\n"
    formatted = [format_agent_line(line, caps) for line in moved]
    return _insert_local_rows(head + new_tail, formatted, caps)


def _insert_local_rows(text: str, rows: list[str], caps: ParserCaps) -> str:
    if "<!-- local-agent-lane:begin -->" not in text:
        stub = (
            "### Local agent (This Computer)\n\n"
            "<!-- local-agent-lane:begin -->\n"
            "_No local agent items._\n"
            "<!-- local-agent-lane:end -->"
        )
        text = insert_before_stop(text, stub, caps)
    return insert_lane_rows(text, "local-agent-lane", rows)


def _ensure_playbook(text: str, caps: ParserCaps) -> str:
    if "## Child Repo Playbook" in _live_region(text, caps):
        return text
    return insert_before_stop(text, "## Child Repo Playbook", caps)


def _lift_unpicked(text: str, caps: ParserCaps) -> str:
    """Legacy mode ignores lane bullets. Number them inside the playbook."""
    if "## Child Repo Playbook" not in text:
        text = _ensure_playbook(text, caps)
    picked = set(child_picks(text, caps))
    moved: list[str] = []
    kept: list[str] = []
    in_details = False
    stopped = False
    for line in text.splitlines():
        if "<details>" in line:
            in_details = True
        is_stop = any(line.startswith(prefix) for prefix in caps.stop_prefixes)
        match = None if in_details or stopped or line.lstrip().startswith(">") else _CANDIDATE.match(line.strip())
        bullet = line.strip()[:1] in "-*"
        if match and match.group("task").strip() not in picked and (bullet or not caps.has_slim):
            moved.append(line.strip())
        else:
            kept.append(line)
        if is_stop and not in_details:
            stopped = True
        if "</details>" in line:
            in_details = False
    if not moved:
        return text
    numbered: list[str] = []
    for index, line in enumerate(moved, start=1):
        body = format_agent_line(line, caps)
        body = re.sub(r"^[-*]\s+", "", body)
        body = re.sub(r"^\d+[a-z]?\.\s+", "", body)
        numbered.append(f"{index}. {body}")
    sprint = "### Sprint — Visible queue\n\n" + "\n".join(numbered)
    body = "\n".join(kept)
    if text.endswith("\n"):
        body += "\n"
    at = body.find("## Child Repo Playbook")
    if at < 0:
        return text
    line_end = body.find("\n", at)
    if line_end < 0:
        return body + "\n\n" + sprint + "\n"
    return body[: line_end + 1] + "\n" + sprint + "\n" + body[line_end + 1 :]


def _adapt_unpicked(text: str, caps: ParserCaps) -> str:
    picked = set(child_picks(text, caps))
    changed = False
    lines: list[str] = []
    for line in text.splitlines():
        match = _CANDIDATE.match(line.strip())
        if match and match.group("task").strip() not in picked and not line.lstrip().startswith(">"):
            rewritten = format_agent_line(line, caps)
            changed = changed or rewritten != line.strip()
            lines.append(rewritten)
        else:
            lines.append(line)
    if not changed:
        return text
    rejoined = "\n".join(lines)
    return rejoined + ("\n" if text.endswith("\n") else "")
