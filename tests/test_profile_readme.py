from __future__ import annotations

from argus.models import (
    Confidence,
    RepoPlan,
    RepoRecord,
    RepoStatus,
    ScoreResult,
)
from argus.profile_readme import MARKER, compose_profile_readme, needs_profile_update


def _plan(full: str, *, topics: list[str] | None = None, attention: float = 10) -> RepoPlan:
    owner, name = full.split("/", 1)
    return RepoPlan(
        repo=RepoRecord(
            full_name=full,
            owner=owner,
            name=name,
            status=RepoStatus.ACTIVE,
            topics=list(topics or []),
            html_url=f"https://github.com/{full}",
            description=f"Desc for {name}",
        ),
        score=ScoreResult(attention=attention, confidence=Confidence.HIGH, category_scores={}),
    )


def test_compose_includes_marker_and_live_topics():
    body = compose_profile_readme(
        user={"login": "alice", "name": "Alice", "bio": "Builder", "location": "Earth"},
        plans=[
            _plan("alice/tools", topics=["python", "automation"], attention=80),
            _plan("alice/lib", topics=["python"], attention=40),
            _plan("alice/alice", topics=["profile"], attention=1),
        ],
        config={
            "tagline": "Ship tools",
            "about": "I build things.",
            "roles": [{"title": "Builder", "blurb": "Daily tools"}],
            "capabilities": [{"title": "Automation", "blurb": "Cron and sync"}],
            "principles": "Keep it maintainable.",
            "open_to": "Collab",
            "max_languages": 5,
            "max_featured_repos": 3,
        },
    )
    assert MARKER in body
    assert "Alice" in body
    assert "python" in body.lower() or "automation" in body.lower()
    assert "alice/tools" in body or "tools" in body
    assert "Suggested pins" in body


def test_needs_update():
    body = compose_profile_readme(
        user={"login": "bob"},
        plans=[],
        config={"about": "Hi", "principles": "P", "open_to": "O"},
    )
    assert needs_profile_update(None, body)
    assert not needs_profile_update(body, body)
    assert needs_profile_update("old without marker", body)
