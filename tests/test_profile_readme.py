from __future__ import annotations

from argus.models import (
    Confidence,
    RepoPlan,
    RepoRecord,
    RepoStatus,
    ScoreResult,
)
from argus.profile_banner import render_banner_svg
from argus.profile_featured import select_featured
from argus.profile_readme import MARKER, compose_profile_readme, needs_profile_update
from argus.profile_skills import bio_is_distinct, resolve_roles_and_capabilities
from argus.profile_stack import ranked_languages


def _plan(
    full: str,
    *,
    topics: list[str] | None = None,
    attention: float = 10,
    stars: int = 0,
    traffic_views: int = 0,
    icon: str | None = None,
    languages: dict[str, int] | None = None,
    description: str | None = None,
) -> RepoPlan:
    owner, name = full.split("/", 1)
    raw: dict = {"stargazers_count": stars, "argus_traffic_views": traffic_views}
    if icon:
        raw["argus_icon_url"] = icon
    if languages:
        raw["argus_languages"] = languages
    return RepoPlan(
        repo=RepoRecord(
            full_name=full,
            owner=owner,
            name=name,
            status=RepoStatus.ACTIVE,
            topics=list(topics or []),
            html_url=f"https://github.com/{full}",
            description=description or f"Desc for {name}",
            raw=raw,
        ),
        score=ScoreResult(attention=attention, confidence=Confidence.HIGH, category_scores={}),
    )


def test_featured_ranks_by_stars_then_traffic_not_attention():
    plans = [
        _plan("alice/noisy", attention=99, stars=1, traffic_views=1),
        _plan("alice/popular", attention=5, stars=50, traffic_views=10),
        _plan("alice/busy", attention=80, stars=50, traffic_views=200),
        _plan("alice/alice", attention=1, stars=999),
    ]
    featured = select_featured(plans, limit=3)
    assert [f["short"] for f in featured] == ["busy", "popular", "noisy"]
    assert featured[0]["stars"] == "50"
    assert featured[0]["traffic"] == "200"
    assert featured[0]["visual"] == "og"


def test_ranked_languages_from_api_bytes():
    rows = ranked_languages({"Python": 9000, "Kotlin": 4000, "Brainfuck": 1}, limit=5)
    assert [r["name"] for r in rows] == ["Python", "Kotlin"]
    assert "devicon" in rows[0]["icon_url"]


def test_compose_portfolio_html_no_traffic_or_topics():
    body = compose_profile_readme(
        user={"login": "alice", "name": "Alice", "bio": "Just vibes.", "location": "Earth"},
        plans=[
            _plan(
                "alice/tools",
                topics=["python", "automation"],
                stars=3,
                icon="https://example.com/tools.png",
                languages={"Python": 5000},
            ),
            _plan(
                "alice/lib",
                topics=["python"],
                stars=30,
                icon="https://example.com/lib.png",
                languages={"Python": 2000, "TypeScript": 1000},
            ),
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
            "include_badges": True,
            "banner_carries_identity": True,
            "featured_card_width": 280,
        },
    )
    assert MARKER in body
    assert 'align="center"' in body
    assert "devicon" in body
    assert "https://example.com/lib.png" in body
    assert body.index("lib.png") < body.index("tools.png")
    assert "traffic" not in body.lower()
    assert "Suggested pins" not in body
    assert "**Topics:**" not in body
    assert "argus-banner.svg" in body
    assert "Just vibes" not in body
    assert "# Alice" not in body  # banner carries identity


def test_auto_skills_when_roles_empty():
    plans = [
        _plan("alice/bot", topics=["automation"], languages={"Python": 8000}, stars=2),
        _plan("alice/app", topics=["android"], languages={"Kotlin": 6000}, stars=5),
    ]
    roles, caps, used_auto = resolve_roles_and_capabilities(
        plans, {"roles": [], "capabilities": []}
    )
    assert used_auto
    assert roles
    assert caps
    body = compose_profile_readme(
        user={"login": "alice", "name": "Alice"},
        plans=plans,
        config={
            "tagline": "Portfolio",
            "about": "",
            "roles": [],
            "capabilities": [],
            "principles": "P",
            "open_to": "O",
            "max_featured_repos": 2,
            "banner_carries_identity": False,
        },
    )
    assert "Problem Solver" in body or "Builder" in body or "Automator" in body
    assert "traffic" not in body.lower()


def test_bio_skip_throwaway():
    assert not bio_is_distinct("Serious about.", "Just vibes.")
    assert not bio_is_distinct("Serious about.", "hi")
    assert bio_is_distinct("Serious about.", "I ship FOSS Android tools.")


def test_featured_app_icon_vs_og():
    plans = [
        _plan("alice/app", stars=10, icon="https://cdn.example/app.png"),
        _plan("alice/lib", stars=5),  # OG fallback
    ]
    featured = select_featured(plans, limit=2)
    assert featured[0]["visual"] == "icon"
    assert featured[1]["visual"] == "og"


def test_banner_svg_contains_name():
    svg = render_banner_svg("Alice", "Ship tools")
    assert "Alice" in svg
    assert "Ship tools" in svg
    assert "#0f766e" in svg or "2dd4bf" in svg


def test_needs_update():
    body = compose_profile_readme(
        user={"login": "bob"},
        plans=[],
        config={"about": "Hi", "principles": "P", "open_to": "O"},
    )
    assert needs_profile_update(None, body)
    assert not needs_profile_update(body, body)
    assert needs_profile_update("old without marker", body)
