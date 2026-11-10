from __future__ import annotations

import json
from pathlib import Path

from argus.rules_sync import (
    block_mutations,
    bump_ref,
    compute_local_tree,
    diff_lock,
    rules_stale,
    sync_lock,
)


def test_sync_and_stale(tmp_path: Path):
    (tmp_path / "config").mkdir()
    fixes = tmp_path / "config" / "fixes"
    fixes.mkdir()
    (fixes / "a.yaml").write_text("id: x\n", encoding="utf-8")
    up = {
        "mode": "pinned",
        "parent": "org/parent",
        "ref": "v1",
        "rules_paths": ["config/fixes"],
    }
    (tmp_path / "argus.upstream.json").write_text(json.dumps(up), encoding="utf-8")
    lock = sync_lock(root=tmp_path)
    assert lock["tree_sha256"]
    assert not rules_stale(tmp_path)
    assert not block_mutations(tmp_path)
    (fixes / "a.yaml").write_text("id: changed\n", encoding="utf-8")
    assert rules_stale(tmp_path)
    assert block_mutations(tmp_path)
    d = diff_lock(tmp_path)
    assert d["stale"]
    assert d["current"] != d["locked"]


def test_bump_pins(tmp_path: Path):
    (tmp_path / "argus.upstream.json").write_text(
        json.dumps({"mode": "live", "ref": "main", "rules_paths": []}),
        encoding="utf-8",
    )
    data = bump_ref("v9.9.9", root=tmp_path)
    assert data["mode"] == "pinned"
    assert data["ref"] == "v9.9.9"
    assert compute_local_tree(tmp_path)  # empty paths still hashes
