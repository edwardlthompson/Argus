from __future__ import annotations

from argus.apply_history import append_local_history


def test_append_local_history(tmp_path):
    entry = {
        "ts": "2026-11-05T00:00:00+00:00",
        "mode": "fix",
        "dry_run": False,
        "applied": ["a/b:HYGIENE-TOPICS"],
        "opened_prs": ["https://example.test/pr/1"],
        "would_prs": [],
        "errors": [],
        "health": {"before": {"open_fixes": 10}, "after": {"open_fixes": 9}},
    }
    jsonl, md = append_local_history(entry, dist_dir=tmp_path)
    assert jsonl.exists()
    assert "HYGIENE-TOPICS" in jsonl.read_text(encoding="utf-8")
    text = md.read_text(encoding="utf-8")
    assert "Argus apply history" in text
    assert "a/b:HYGIENE-TOPICS" in text
