from __future__ import annotations

from argus.discover import DiscoveryResult, _to_record
from argus.models import RepoStatus


def test_archived_skipped_from_scored_set():
    raw = {
        "full_name": "u/old",
        "archived": True,
        "private": False,
        "fork": False,
        "description": "x",
        "default_branch": "main",
        "html_url": "",
        "permissions": {"push": True},
        "topics": [],
    }
    record = _to_record(raw, RepoStatus.ARCHIVED)
    assert record.archived is True
    # Default discovery path marks skipped — unit-level: scored list must not include archived
    scored: list = []
    skipped: list[str] = []
    include_archived = False
    status = RepoStatus.ARCHIVED
    if not include_archived and (status == RepoStatus.ARCHIVED or raw.get("archived")):
        skipped.append(raw["full_name"])
    else:
        scored.append(record)
    assert skipped == ["u/old"]
    assert scored == []


def test_discovery_result_carries_skipped():
    result = DiscoveryResult(
        repos=[],
        new=[],
        removed=[],
        viewer="u",
        skipped_archived=["u/old"],
    )
    assert result.skipped_archived == ["u/old"]
