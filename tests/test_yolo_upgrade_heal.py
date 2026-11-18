"""Unit: TEMPLATE_INDEX heal mutations (no network)."""

from __future__ import annotations

from argus.yolo_upgrade_heal import INDEX_ENTRIES, TARGET_VER


def test_index_entries_cover_argus_workflows():
    assert ".github/workflows/argus-remote-stub.yml" in INDEX_ENTRIES
    assert ".github/workflows/argus-rules-manifest.yml" in INDEX_ENTRIES
    assert TARGET_VER == "1.13.0"
