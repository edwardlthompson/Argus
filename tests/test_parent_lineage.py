from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_parent_lineage_files_exist():
    assert (ROOT / ".template-version").read_text(encoding="utf-8").strip() == "1.12.0"
    update = (ROOT / ".template-update.json").read_text(encoding="utf-8")
    assert "edwardlthompson/agent-project-bootstrap" in update
    assert (ROOT / "bootstrap.config.json").exists()
    assert (ROOT / "AGENTS.md").exists()
    assert (ROOT / "docs" / "PARENT_GAP_LIST.md").exists()
    gap = (ROOT / "docs" / "PARENT_GAP_LIST.md").read_text(encoding="utf-8")
    assert "| 🔲 |" not in gap  # no open gap rows
    assert (ROOT / ".agent" / "AGENT_MEMORY.md").exists()
    assert (ROOT / "SECURITY.md").exists()
