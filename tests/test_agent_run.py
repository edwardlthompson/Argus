from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_agent_run():
    path = Path(__file__).resolve().parents[1] / "scripts" / "agent-run.py"
    spec = importlib.util.spec_from_file_location("agent_run_shim", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_verify_and_na_disjoint():
    mod = _load_agent_run()
    assert mod.VERIFY_VERBS.isdisjoint(mod.NA_VERBS)


def test_unknown_verb_exits_2():
    mod = _load_agent_run()
    assert mod.main(["definitely-not-a-verb"]) == 2


def test_na_verb_exits_0(capsys):
    mod = _load_agent_run()
    assert mod.main(["feature-gate"]) == 0
    out = capsys.readouterr().out
    assert "N/A" in out
    assert "G12" in out


def test_check_cursor_hooks_smoke():
    mod = _load_agent_run()
    assert mod.main(["check-cursor-hooks", "--smoke"]) == 0


def test_build_sprint_status_prints_row(capsys):
    mod = _load_agent_run()
    assert mod.main(["build-sprint-status"]) == 0
    assert capsys.readouterr().out.strip()
