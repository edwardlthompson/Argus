from __future__ import annotations

from pathlib import Path

from argus.notify import build_summary
from argus.notify_log import append_notification_log
from argus.pipeline import build_plans_from_fixtures
from tests.conftest import load_fixture


def test_build_summary_uses_counts_and_links_not_cves(monkeypatch):
    monkeypatch.delenv("GITHUB_RUN_ID", raising=False)
    plans = build_plans_from_fixtures([load_fixture("human_only.json")])
    text = build_summary(
        plans,
        report_url="https://example.github.io/Argus/",
        inbox_url="https://github.com/edwardlthompson/Argus/issues?q=label%3Aargus-inbox",
        run_url="https://github.com/edwardlthompson/Argus/actions",
    )
    assert "Argus needs you" in text
    assert "Inbox:" in text
    assert "Actions" in text
    assert "CVE" not in text
    assert "secret scanning" not in text.lower()


def test_notify_log_caps_and_omits_repo_names(tmp_path: Path):
    path = tmp_path / "notifications.json"
    for i in range(5):
        append_notification_log(
            {
                "human_count": i,
                "channels": ["discord"],
                "run_url": "https://github.com/x/y/actions/runs/1",
                "inbox_url": "https://github.com/x/y/issues",
            },
            path=path,
            cap=3,
        )
    import json

    rows = json.loads(path.read_text(encoding="utf-8"))
    assert len(rows) == 3
    assert "repo" not in rows[-1]
    assert rows[-1]["human_count"] == 4
