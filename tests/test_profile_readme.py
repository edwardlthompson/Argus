from __future__ import annotations

from argus.models import (
    Confidence,
    RepoPlan,
    RepoRecord,
    RepoStatus,
    ScoreResult,
)
from argus.profile_featured import select_featured
from argus.profile_readme import MARKER, compose_profile_readme, needs_profile_update


def _plan(
    full: str,
    *,
    topics: list[str] | None = None,
    attention: float = 10,
    stars: int = 0,
    traffic_views: int = 0,
    icon: str | None = None,
) -> RepoPlan:
    owner, name = full.split("/", 1)
    raw: dict = {"stargazers_count": stars, "argus_traffic_views": traffic_views}
    if icon:
        raw["argus_icon_url"] = icon
    return RepoPlan(
        repo=RepoRecord(
            full_name=full,
            owner=owner,
            name=name,
            status=RepoStatus.ACTIVE,
            topics=list(topics or []),
            html_url=f"https://github.com/{full}",
            description=f"Desc for {name}",
            raw=raw,
        ),
        score=ScoreResult(attention=attention, confidence=Confidence.HIGH, category_scores={}),
    )


def test_featured_ranks_by_stars_then_traffic_not_attention():
    plans = [
        _plan("alice/noisy", attention=99, stars=1, traffic_views=1),
        _plan("alice/popular", attention=5, stars=50, traffic_views=10),
        _plan("alice/busy", attention=80, stars=50, traffic_views=200),
        _plan("alice/alice", attention=1, stars=999),  # profile repo excluded
    ]
    featured = select_featured(plans, limit=3)
    assert [f["short"] for f in featured] == ["busy", "popular", "noisy"]
    assert featured[0]["stars"] == "50"
    assert featured[0]["traffic"] == "200"


def test_compose_includes_icons_and_star_ranking():
    body = compose_profile_readme(
        user={"login": "alice", "name": "Alice", "bio": "Builder", "location": "Earth"},
        plans=[
            _plan(
                "alice/tools",
                topics=["python", "automation"],
                attention=80,
                stars=3,
                icon="https://example.com/tools.png",
            ),
            _plan(
                "alice/lib",
                topics=["python"],
                attention=40,
                stars=30,
                icon="https://example.com/lib.png",
            ),
            _plan("alice/alice", topics=["profile"], attention=1, stars=1),
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
    assert "https://example.com/lib.png" in body
    assert body.index("lib.png") < body.index("tools.png")
    assert "★30" in body or "★30" in body.replace(" ", "")
    assert "Suggested pins" not in body


def test_needs_update():
    body = compose_profile_readme(
        user={"login": "bob"},
        plans=[],
        config={"about": "Hi", "principles": "P", "open_to": "O"},
    )
    assert needs_profile_update(None, body)
    assert not needs_profile_update(body, body)
    assert needs_profile_update("old without marker", body)
