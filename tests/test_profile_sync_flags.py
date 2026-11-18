"""Overview sync_profile is independent of YOLO skip_profile mutations."""

from __future__ import annotations


def test_weekly_yml_passes_with_profile():
    from pathlib import Path

    text = Path(".github/workflows/weekly.yml").read_text(encoding="utf-8")
    assert "--with-profile" in text
    assert "argus run --with-profile" in text or "argus run --apply --with-profile" in text


def test_enrich_refreshes_private_flag(monkeypatch):
    from argus.models import Confidence, RepoPlan, RepoRecord, RepoStatus, ScoreResult
    from argus.profile_enrich import enrich_plans_for_profile

    plan = RepoPlan(
        repo=RepoRecord(
            full_name="acme/was-public",
            owner="acme",
            name="was-public",
            status=RepoStatus.ACTIVE,
            private=False,
            raw={"stargazers_count": 9},
        ),
        score=ScoreResult(attention=1.0, confidence=Confidence.HIGH, category_scores={}),
    )

    class Client:
        def get_repo(self, owner: str, name: str):
            return {
                "private": True,
                "archived": False,
                "stargazers_count": 9,
                "forks_count": 1,
                "subscribers_count": 0,
                "description": "now private",
                "default_branch": "main",
                "html_url": f"https://github.com/{owner}/{name}",
            }

        def get(self, path: str):  # pragma: no cover
            raise AssertionError("traffic should not run for private")

    enrich_plans_for_profile(Client(), [plan], profile_login="acme")  # type: ignore[arg-type]
    assert plan.repo.private is True
    assert plan.repo.raw.get("private") is True
