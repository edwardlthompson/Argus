from __future__ import annotations

from argus.agent_dispatch import _mechanical_ids_applied


def test_mechanical_ids_independent(tmp_path):
    (tmp_path / "AGENT_MEMORY.md").write_text("# mem\n", encoding="utf-8")
    (tmp_path / "BUILD_PLAN.md").write_text("# Custom board\n\n1. 🔲 [HUMAN] Do the thing\n", encoding="utf-8")
    applied = _mechanical_ids_applied(
        tmp_path, {"AGENT-MEMORY-LAYOUT", "BOARD-RESTRUCTURE"}
    )
    assert applied == {"AGENT-MEMORY-LAYOUT", "BOARD-RESTRUCTURE"}


def test_mechanical_board_does_not_resolve_memory(tmp_path):
    (tmp_path / "BUILD_PLAN.md").write_text("# Custom board\n\n1. 🔲 [AGENT] Work\n", encoding="utf-8")
    applied = _mechanical_ids_applied(
        tmp_path, {"AGENT-MEMORY-LAYOUT", "BOARD-RESTRUCTURE"}
    )
    assert applied == {"BOARD-RESTRUCTURE"}
    assert not (tmp_path / ".agent" / "AGENT_MEMORY.md").exists()


def test_mechanical_memory_does_not_resolve_board(tmp_path):
    (tmp_path / "AGENT_MEMORY.md").write_text("# mem\n", encoding="utf-8")
    applied = _mechanical_ids_applied(
        tmp_path, {"AGENT-MEMORY-LAYOUT", "BOARD-RESTRUCTURE"}
    )
    assert applied == {"AGENT-MEMORY-LAYOUT"}
    assert not (tmp_path / "BUILD_PLAN.md").exists()
