"""explain_repo unit test with fake client."""

from __future__ import annotations

from typing import Any

from argus.explain import explain_repo


class Fake:
    def get_repo(self, owner: str, name: str) -> dict[str, Any]:
        return {
            "full_name": f"{owner}/{name}",
            "private": False,
            "archived": False,
            "fork": False,
            "description": "x",
            "default_branch": "main",
            "html_url": f"https://github.com/{owner}/{name}",
            "topics": [],
        }

    def get(self, path: str, **kwargs: Any) -> Any:
        raise Exception("boom")  # noqa: BLE001 — collectors catch GitHubError only


def test_explain_tolerates_missing_signals(monkeypatch) -> None:
    from argus import explain as expl
    from argus.models import Confidence, SignalBundle
    from argus.score import ScoreResult

    monkeypatch.setattr(expl, "collect_signals", lambda c, r: SignalBundle())
    monkeypatch.setattr(
        expl,
        "score_repo",
        lambda s, rub, st: ScoreResult(attention=12.0, confidence=Confidence.LOW, category_scores={}, notes=["n"]),
    )
    monkeypatch.setattr(expl, "load_rubric", lambda: {"weights": {}})
    out = explain_repo(Fake(), "a/b")  # type: ignore[arg-type]
    assert out["repo"] == "a/b"
    assert out["attention"] == 12.0
