"""Worktree GC + prompt budget."""

from argus.agent_ops import gc_worktrees, prompt_budget_report


def test_gc_worktrees_dry(tmp_path):
    d = tmp_path / "wt"
    (d / "a").mkdir(parents=True)
    out = gc_worktrees(apply=False, root=d)
    assert out["kept"] == ["a"]
    assert (d / "a").exists()
    out2 = gc_worktrees(apply=True, root=d)
    assert out2["removed"] == ["a"]
    assert not (d / "a").exists()


def test_prompt_budget():
    r = prompt_budget_report({"o/r": "x" * 10}, max_chars=5)
    assert r["prompts"][0]["over_budget"] is True
