from __future__ import annotations

from argus.apply import HANDLERS, _topics_for
from argus.models import Confidence, RepoPlan, RepoRecord, RepoStatus, ScoreResult


def test_topics_helper_fills_three():
    repo = RepoRecord(
        full_name="u/my-cool-app",
        owner="u",
        name="my-cool-app",
        status=RepoStatus.ACTIVE,
        topics=["foss"],
    )
    plan = RepoPlan(
        repo=repo,
        score=ScoreResult(attention=1, confidence=Confidence.HIGH, category_scores={}),
    )
    topics = _topics_for(plan)
    assert len(topics) >= 3
    assert "foss" not in topics


def test_handlers_cover_core_auto_safe():
    for fid in (
        "HYGIENE-TOPICS",
        "HYGIENE-DESCRIPTION",
        "HYGIENE-SECURITY-MD",
        "LINEAGE-VERSION-STALE",
        "BOARD-MARKERS",
    ):
        assert fid in HANDLERS
