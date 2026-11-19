"""Child /build visibility. Parsers below are frozen copies, not imports of a child repo."""

from __future__ import annotations

import re

from argus.board_normalize import append_missing_markers, restructure_divergent
from argus.board_queue import (
    ParserCaps,
    caps_from_sources,
    child_picks,
    ensure_queue_visible,
    invisible_open_rows,
    legacy_active,
)

OPEN = r"(?:🔲|⬜|\[ \])"
# HermesLauncher / QRaft era: venue tag is not optional. Space after ] is required.
OLD_BULLET = re.compile(rf"^- {OPEN} \[(?:AGENT|AUTO|HUMAN|ADB)\]\s+(.+)$")
OLD_NUMBERED = re.compile(rf"^(?:\d+[a-z]?)\.\s+{OPEN}\s+\[(?:AGENT|AUTO|HUMAN|ADB)\]\s+(.+)$")
# Current APB: optional [LOCAL]|[CLOUD], then whitespace.
NEW_BULLET = re.compile(
    rf"^- {OPEN} \[(?:AGENT|AUTO|HUMAN|ADB)\](?:\[(?:LOCAL|CLOUD)\])?\s+(.+)$"
)
NEW_NUMBERED = re.compile(
    rf"^(?:\d+[a-z]?)\.\s+{OPEN}\s+\[(?:AGENT|AUTO|HUMAN|ADB)\](?:\[(?:LOCAL|CLOUD)\])?\s+(.+)$"
)

OLD_MODEL = """
ROW_BULLET = re.compile(
    rf"^- {OPEN} \\[(?P<owner>AGENT|AUTO|HUMAN|ADB)\\]\\s+(?P<task>.+)$"
)
"""
NEW_MODEL = """
ROW_BULLET = re.compile(
    rf"^- {OPEN} \\[(?P<owner>AGENT|AUTO|HUMAN|ADB)\\]"
    rf"(?:\\[(?P<venue>LOCAL|CLOUD)\\])?\\s+(?P<task>.+)$"
)
"""
CHILD_SRC = """
def uses_legacy_playbook(text: str) -> bool:
    return "## Child Repo Playbook" in text or "#### Sequential" in text
"""
SLIM_PARSE = """
def parse_numbered_board(text: str):
    for line in text.splitlines():
        if line.startswith("## Ongoing Maintenance") or line.startswith("## Archive"):
            break
"""
ANCIENT_PARSE = """
def parse_maintainer_active_board(text: str):
    if line.startswith("## Template Maintainer"):
        return [], []
"""

NO_VENUE = ParserCaps(venue=False)
ANCIENT = ParserCaps(venue=False, has_slim=False, has_legacy=True)


def _stop(line: str) -> bool:
    return line.startswith("## Archive") or line.startswith("## Ongoing Maintenance")


def frozen_slim(text: str, *, venue: bool) -> list[str]:
    bullet, numbered = (NEW_BULLET, NEW_NUMBERED) if venue else (OLD_BULLET, OLD_NUMBERED)
    tasks: list[str] = []
    for line in text.splitlines():
        if _stop(line):
            break
        match = numbered.match(line) or bullet.match(line)
        if match:
            tasks.append(match.group(1).strip())
    return tasks


def frozen_legacy(text: str, *, venue: bool) -> list[str]:
    """Playbook mode: numbered rows inside sprint blocks only. Lanes are ignored."""
    if "## Child Repo Playbook" not in text and "#### Sequential" not in text:
        return frozen_slim(text, venue=venue)
    numbered = NEW_NUMBERED if venue else OLD_NUMBERED
    tasks: list[str] = []
    in_child = False
    in_sprint = False
    for line in text.splitlines():
        if line.strip().startswith("## Child Repo Playbook"):
            in_child = True
            continue
        if not in_child:
            continue
        if line.startswith("## Ongoing Maintenance") or (
            line.startswith("## ") and not line.startswith("### ")
        ):
            if line.startswith("## Ongoing Maintenance"):
                break
            in_sprint = False
            continue
        if line.startswith("### Sprint"):
            in_sprint = True
            continue
        if in_sprint:
            match = numbered.match(line)
            if match:
                tasks.append(match.group(1).strip())
    return tasks


def _lane_before_stop(text: str) -> bool:
    lines = text.splitlines()
    stop = next((i for i, line in enumerate(lines) if _stop(line)), None)
    begins = [
        i
        for i, line in enumerate(lines)
        if "local-agent-lane:begin" in line or "cloud-agent-lane:begin" in line
    ]
    assert begins
    return stop is None or all(i < stop for i in begins)


MEDIA3 = """# Build Plan

## Ongoing Maintenance

Weekly health check.

## Archived Sprints

### Local agent (This Computer)

Standing queue. Rows: `🔲 [AGENT][LOCAL] …`.

<!-- local-agent-lane:begin -->
- 🔲 [AGENT][LOCAL] Media3 bump + signed APK release — scope: examples/android/
<!-- local-agent-lane:end -->

### Cloud agent (Cursor Cloud)

<!-- cloud-agent-lane:begin -->
_No cloud agent items._
<!-- cloud-agent-lane:end -->
"""

QRAFT_OLD = """# Build Plan

## Child Repo Playbook

### Sprint 13 — PWA + adaptive UX

#### Sequential

1. 🔲 [AGENT] Stale sprint 13 leftover — scope: web/

#### Parallel

2. 🔲 [AGENT] Parallel-only row — scope: web/
"""


def test_caps_detect_venue_slim_and_legacy():
    old = caps_from_sources(model=OLD_MODEL, child=CHILD_SRC, parse=SLIM_PARSE)
    new = caps_from_sources(model=NEW_MODEL, child=CHILD_SRC, parse=SLIM_PARSE)
    ancient = caps_from_sources(model=OLD_MODEL, child=CHILD_SRC, parse=ANCIENT_PARSE)
    assert old.venue is False
    assert new.venue is True
    assert old.has_slim is True
    assert ancient.has_slim is False
    assert old.legacy_triggers == ("## Child Repo Playbook", "#### Sequential")
    assert old.stop_prefixes == ("## Ongoing Maintenance", "## Archive")


def test_lanes_below_archive_move_above_stop_and_old_parser_sees_them():
    out = ensure_queue_visible(MEDIA3, NO_VENUE)
    assert _lane_before_stop(out)
    assert out.index("local-agent-lane:begin") < out.index("## Ongoing Maintenance")
    assert "- 🔲 [AGENT] Media3 bump + signed APK release — scope: examples/android/" in out
    picked = frozen_slim(out, venue=False)
    assert any("Media3 bump + signed APK release" in task for task in picked)
    assert child_picks(out, NO_VENUE) == picked
    assert invisible_open_rows(out, NO_VENUE) == []
    assert invisible_open_rows(MEDIA3, NO_VENUE)


def test_append_inserts_missing_lanes_before_archived_sprints():
    board = """# Build Plan

## News inbox (synced)

- 🔲 [AGENT] Flag idle Dependabot pause — scope: argus/signals
- 🔲 [HUMAN] Review issue types for triage

## Archived Sprints

Old notes.
"""
    out = append_missing_markers(board, caps=NO_VENUE)
    assert _lane_before_stop(out)
    assert "News inbox (synced)" not in out
    assert "- 🔲 [AGENT] Flag idle Dependabot pause — scope: argus/signals" in out
    assert "[AGENT][LOCAL]" not in out
    assert "Review issue types" in out
    assert out.index("Waiting on a person") < out.index("## Archived Sprints")
    assert any("Flag idle Dependabot pause" in task for task in frozen_slim(out, venue=False))
    assert append_missing_markers(out, caps=NO_VENUE) == out


def test_venue_parser_keeps_local_tag_and_current_regex():
    out = ensure_queue_visible(MEDIA3, ParserCaps(venue=True))
    assert "- 🔲 [AGENT][LOCAL] Media3 bump + signed APK release — scope: examples/android/" in out
    assert any("Media3 bump" in task for task in frozen_slim(out, venue=True))
    assert not any("Media3 bump" in task for task in frozen_slim(MEDIA3, venue=False))


def test_preserved_board_does_not_trip_legacy_mode():
    files = restructure_divergent(QRAFT_OLD, source_path="BUILD_PLAN.md", has_completed_tasks=False, caps=NO_VENUE)
    root = files["BUILD_PLAN.md"]
    assert "## Child Repo Playbook" not in root
    assert "#### Sequential" not in root
    assert "Child Repo" in root
    assert not legacy_active(root, NO_VENUE)
    assert _lane_before_stop(root)
    live_text, _, quoted = root.partition("## Archive")
    live = frozen_slim(root, venue=False)
    assert any("Stale sprint 13 leftover" in task for task in live)
    assert any("Stale sprint 13 leftover" in line for line in live_text.splitlines())
    assert not any(line.startswith("1. 🔲") and "Stale sprint 13" in line for line in quoted.splitlines())
    # The quoted sprint heading is still human-readable, but it is not a parseable trigger.
    assert "Sprint 13" in quoted
    assert quoted.lstrip().startswith("<summary>Previous board</summary>") or "> " in quoted
    assert frozen_legacy(root, venue=False) == live
    assert invisible_open_rows(root, NO_VENUE) == []


def test_raw_details_quote_is_flagged_then_repaired():
    damaged = """# Build Plan

<!-- remaining-tally -->
**Remaining:** (tally on next sync)
<!-- /remaining-tally -->

<!-- open-prs-sync:begin -->
_No open Dependabot or Release Please PRs._
<!-- open-prs-sync:end -->

<!-- template-gaps-sync:begin -->
_No template gaps._
<!-- template-gaps-sync:end -->

### Local agent (This Computer)

<!-- local-agent-lane:begin -->
- 🔲 [AGENT][LOCAL] Restore examples/web — scope: examples/web
<!-- local-agent-lane:end -->

<!-- cloud-agent-lane:begin -->
_No cloud agent items._
<!-- cloud-agent-lane:end -->

## Archive

<details>
<summary>Previous board</summary>

## Child Repo Playbook

### Sprint 13 — PWA

#### Sequential

1. 🔲 [AGENT] Stale sprint 13 leftover — scope: web/

</details>
"""
    assert any("legacy" in row for row in invisible_open_rows(damaged, NO_VENUE))
    assert legacy_active(damaged, NO_VENUE)
    # Legacy mode reads the quoted sprint and ignores the lane, which is the QRaft failure.
    assert any("Stale sprint 13" in task for task in frozen_legacy(damaged, venue=False))
    assert not any("Restore examples/web" in task for task in frozen_legacy(damaged, venue=False))
    fixed = ensure_queue_visible(damaged, NO_VENUE)
    assert not legacy_active(fixed, NO_VENUE)
    assert any("Restore examples/web" in task for task in frozen_slim(fixed, venue=False))
    assert not any("Stale sprint 13" in task for task in frozen_slim(fixed, venue=False))
    assert invisible_open_rows(fixed, NO_VENUE) == []


def test_legacy_playbook_gets_numbered_agent_rows():
    board = """# Build Plan

## Child Repo Playbook

### Sprint 1 — Already open

#### Sequential

1. 🔲 [AGENT] Keep the existing sprint row — scope: app/

## News inbox (synced)

- 🔲 [AGENT][LOCAL] Media3 bump + signed APK release — scope: examples/android/

## Ongoing Maintenance

- 🔲 [AUTO] Weekly health
"""
    out = append_missing_markers(board, caps=NO_VENUE)
    assert legacy_active(out, NO_VENUE)
    picked = frozen_legacy(out, venue=False)
    assert any("Media3 bump + signed APK release" in task for task in picked)
    assert any("Keep the existing sprint row" in task for task in picked)
    assert "[AGENT][LOCAL]" not in out
    media = next(line for line in out.splitlines() if "Media3 bump" in line)
    assert media.startswith("1. 🔲 [AGENT] ")
    assert invisible_open_rows(out, NO_VENUE) == []


HERMES_PARSE_NOISE = '''
def parse_sprint_blocks(text: str):
    if line.strip().startswith("## Child Repo Playbook"):
        return
    if line.startswith("## ") and not line.startswith("### "):
        return

def parse_numbered_board(text: str):
    if line.startswith("## Ongoing Maintenance") or line.startswith("## Archive"):
        break
'''

QRAFT_PARSE = '''
def parse_sprint_blocks(text: str):
    if line.strip().startswith("## Child Repo Playbook"):
        in_child = True
    if line.startswith("## Ongoing Maintenance"):
        break
'''

QRAFT_SPRINT = '''
def _child_status(text, progress, backlog_keys):
    for title, block_lines in parse_sprint_blocks(text):
        return title
'''


def test_drifted_parser_does_not_treat_every_h2_as_a_stop():
    """HermesLauncher keeps parse_numbered_board in the child file; parse.py says startswith('## ')."""
    caps = caps_from_sources(model=OLD_MODEL, child=HERMES_PARSE_NOISE, parse=HERMES_PARSE_NOISE)
    assert caps.venue is False
    assert caps.has_slim is True
    assert all(prefix != "## " for prefix in caps.stop_prefixes)
    assert "## Child Repo Playbook" not in caps.stop_prefixes
    assert caps.stop_prefixes == ("## Ongoing Maintenance", "## Archive")
    board = """# Build Plan

### Sprint 55 — Ship Android GitHub Release

1. 🔲 [AGENT] Bump Media3 1.11.0 to 1.11.1 — scope: examples/android/
2. 🔲 [AGENT] Cut/update GitHub Release with signed Android APK/AAB — scope: examples/android/

## Ongoing Maintenance

Not a checklist.

## Archive
"""
    assert child_picks(board, caps) == frozen_slim(board, venue=False)
    assert invisible_open_rows(board, caps) == []
    assert ensure_queue_visible(board, caps) == board


def test_legacy_only_driver_lifts_lane_rows_ahead_of_quoted_sprint():
    caps = caps_from_sources(model=OLD_MODEL, child=None, parse=QRAFT_PARSE, sprint=QRAFT_SPRINT)
    assert caps.has_slim is False
    assert caps.venue is False
    board = """# Build Plan

### Local agent (This Computer)

<!-- local-agent-lane:begin -->
- 🔲 [AGENT][LOCAL] Restore examples/web — scope: examples/web
<!-- local-agent-lane:end -->

## Archive

<details>
<summary>Previous board</summary>

## Child Repo Playbook

### Sprint 13 — PWA

#### Sequential

1. 🔲 [AGENT] Stale sprint 13 leftover — scope: web/

</details>
"""
    assert any("Stale sprint 13" in task for task in frozen_legacy(board, venue=False))
    assert not any("Restore examples/web" in task for task in frozen_legacy(board, venue=False))
    fixed = ensure_queue_visible(board, caps)
    assert fixed.split("## Archive", 1)[0].count("## Child Repo Playbook") == 1
    picked = frozen_legacy(fixed, venue=False)
    assert any("Restore examples/web" in task for task in picked)
    assert not any("Stale sprint 13" in task for task in picked)
    assert invisible_open_rows(fixed, caps) == []
    assert ensure_queue_visible(fixed, caps) == fixed


def test_ancient_parser_without_slim_queue_gets_a_playbook_row():
    board = """# Build Plan

- 🔲 [AGENT][LOCAL] Media3 bump + signed APK release — scope: examples/android/

## Archive

done
"""
    out = ensure_queue_visible(board, ANCIENT)
    assert "## Child Repo Playbook" in out.split("## Archive", 1)[0]
    picked = frozen_legacy(out, venue=False)
    assert any("Media3 bump + signed APK release" in task for task in picked)
    assert invisible_open_rows(out, ANCIENT) == []
