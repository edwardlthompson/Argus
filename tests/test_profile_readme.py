from __future__ import annotations

from argus.models import (
    Confidence,
    RepoPlan,
    RepoRecord,
    RepoStatus,
    ScoreResult,
)
from argus.profile_banner import render_banner_svg
from argus.profile_featured import center_grid_rows, select_featured
from argus.profile_icons import pick_icon_path
from argus.profile_readme import MARKER, compose_profile_readme, needs_profile_update
from argus.profile_skills import bio_is_distinct, resolve_roles_and_capabilities
from argus.profile_stack import grouped_stack, ranked_languages


def _plan(
    full: str,
    *,
    topics: list[str] | None = None,
    attention: float = 10,
    stars: int = 0,
    forks: int = 0,
    watches: int = 0,
    traffic_views: int = 0,
    icon: str | None = None,
    languages: dict[str, int] | None = None,
    description: str | None = None,
) -> RepoPlan:
    owner, name = full.split("/", 1)
    raw: dict = {
        "stargazers_count": stars,
        "forks_count": forks,
        "subscribers_count": watches,
        "argus_traffic_views": traffic_views,
    }
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


def test_featured_ranks_by_views_then_stars_not_attention():
    plans = [
        _plan("alice/noisy", attention=99, stars=1, traffic_views=1),
        _plan("alice/popular", attention=5, stars=50, traffic_views=10),
        _plan("alice/busy", attention=80, stars=50, traffic_views=200),
        _plan("alice/alice", attention=1, stars=999),
        _plan("alice/sleeper", attention=1, stars=99, traffic_views=5),
    ]
    featured = select_featured(plans, limit=3)
    assert [f["short"] for f in featured] == ["busy", "popular", "sleeper"]
    assert featured[0]["views"] == "200"


def test_featured_curated_overrides_ranking():
    plans = [
        _plan("alice/noisy", stars=99, traffic_views=99),
        _plan("alice/flagship", stars=1, traffic_views=0),
        _plan("alice/other", stars=50, traffic_views=10),
    ]
    featured = select_featured(plans, limit=2, curated=["flagship", "other"])
    assert [f["short"] for f in featured] == ["flagship", "other"]


def test_featured_limit_zero_includes_all_eligible():
    plans = [
        _plan("alice/a", stars=1),
        _plan("alice/b", stars=2),
        _plan("alice/c", stars=3),
        _plan("alice/alice", stars=99),
    ]
    featured = select_featured(plans, limit=0, curated=["a"])
    assert [f["short"] for f in featured] == ["a", "c", "b"]


def test_featured_includes_forks():
    from argus.models import Confidence, RepoPlan, RepoRecord, RepoStatus, ScoreResult

    fork = RepoPlan(
        repo=RepoRecord(
            full_name="alice/Google-Messages-For-Desktop",
            owner="alice",
            name="Google-Messages-For-Desktop",
            status=RepoStatus.ACTIVE,
            fork=True,
            html_url="https://github.com/alice/Google-Messages-For-Desktop",
            description="Desktop Google Messages",
            raw={"stargazers_count": 5},
        ),
        score=ScoreResult(attention=1, confidence=Confidence.HIGH, category_scores={}),
    )
    featured = select_featured([fork, _plan("alice/own", stars=1)], limit=0)
    assert "Google-Messages-For-Desktop" in [f["short"] for f in featured]


def test_generate_icon_png_is_png_and_motif_aware():
    from argus.profile_icon_gen import _motif_chat, choose_motif, generate_icon_png

    png = generate_icon_png("Google-Messages-For-Desktop", "FOSS Electron SMS chat app")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 400
    assert choose_motif("Google-Messages-For-Desktop", "chat app") is _motif_chat


def test_center_grid_rows_pads_short_last_row():
    items = [{"short": str(i)} for i in range(10)]
    rows = center_grid_rows(items, 7)
    assert len(rows) == 2
    assert len(rows[0]) == 7
    assert all(c is not None for c in rows[0])
    # 3 leftovers → pad 2 left, 2 right for 7 cols
    assert rows[1][0] is None and rows[1][1] is None
    assert [c["short"] for c in rows[1] if c] == ["7", "8", "9"]
    assert rows[1][-1] is None and rows[1][-2] is None


def test_pick_icon_skips_svg_prefers_png():
    paths = [
        "branding/assets/app-icon-512.svg",
        "docs/brand/logo-official.png",
        "examples/desktop/src-tauri/icons/icon.png",
    ]
    assert pick_icon_path(paths, sizes={"branding/assets/app-icon-512.svg": 878}) == (
        "docs/brand/logo-official.png"
    )
    assert pick_icon_path(["branding/assets/app-icon-512.svg"]) is None


def test_ranked_languages_from_api_bytes():
    rows = ranked_languages({"Python": 9000, "Kotlin": 4000, "Brainfuck": 1}, limit=5)
    assert [r["name"] for r in rows] == ["Python", "Kotlin"]
    assert "devicon" in rows[0]["icon_url"]


def test_grouped_stack_from_langs_and_topics():
    plans = [
        _plan("alice/app", topics=["android"], languages={"Kotlin": 1000}),
        _plan("alice/bot", topics=["automation"], languages={"Python": 2000}),
    ]
    totals = {"Kotlin": 1000, "Python": 2000}
    groups = grouped_stack(
        plans,
        totals,
        groups=[
            {"title": "Languages", "limit": 4, "match": ["python", "kotlin"]},
            {"title": "Mobile", "limit": 4, "match": ["android", "kotlin"]},
            {"title": "Empty", "limit": 4, "match": ["zig"]},
        ],
    )
    titles = [g["title"] for g in groups]
    assert titles == ["Languages", "Mobile"]
    assert any(i["slug"] == "python" for i in groups[0]["icons"])


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
            "max_featured_repos": 0,
            "include_badges": True,
            "banner_carries_identity": True,
            "featured_card_width": 280,
            "show_featured_stars": False,
            "featured_columns": 7,
            "featured_icon_size": 64,
            "current_focus": [{"title": "Now", "blurb": "Shipping"}],
            "open_to_cards": [{"title": "FOSS", "blurb": "PRs welcome"}],
        },
    )
    assert MARKER in body
    assert 'align="center"' in body
    assert "devicon" in body
    assert "https://example.com/lib.png" in body
    assert 'width="64"' in body
    assert 'height="64"' not in body  # avoid vertical stretch
    assert "traffic" not in body.lower()
    assert "Suggested pins" not in body
    assert "Just vibes" not in body
    assert "# Alice" not in body
    assert body.index("## Featured projects") < body.index("## Tech stack")
    assert "./assets/octicons/star-16.svg" in body
    assert 'alt="Views"' in body
    assert "Current focus" in body
    assert "Also open to" in body
    assert "FOSS" in body
    assert "badge/GitHub" in body
    assert 'width="14%"' in body  # 100 // 7


def test_auto_skills_when_roles_empty():
    plans = [
        _plan("alice/bot", topics=["automation"], languages={"Python": 8000}, stars=2),
        _plan("alice/app", topics=["android"], languages={"Kotlin": 6000}, stars=5),
    ]
    roles, caps, used_auto = resolve_roles_and_capabilities(
        plans, {"roles": [], "capabilities": []}
    )
    assert used_auto and roles and caps


def test_bio_skip_throwaway():
    assert not bio_is_distinct("Serious about.", "Just vibes.")
    assert bio_is_distinct("Serious about.", "I ship FOSS Android tools.")


def test_featured_app_icon_vs_og():
    plans = [
        _plan("alice/app", stars=10, icon="https://cdn.example/app.png"),
        _plan("alice/lib", stars=5),
    ]
    featured = select_featured(plans, limit=2)
    assert featured[0]["visual"] == "icon"
    assert featured[1]["visual"] == "og"


def test_pick_icon_skips_golden_path_stub_prefers_mipmap():
    paths = [
        "examples/android/third_party/launcher3/res/drawable/ic_launcher_home.xml",
        "examples/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png",
        "branding/assets/social-preview.svg",
        "branding/assets/app-icon-512.svg",
        "branding/concepts/trendalgo-icon-a.jpg",
    ]
    sizes = {
        "branding/assets/app-icon-512.svg": 231,  # Golden Path stub
        "examples/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png": 31343,
    }
    assert (
        pick_icon_path(paths, sizes=sizes)
        == "examples/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png"
    )
    assert (
        pick_icon_path(
            [
                "apps/mobile/fastlane/metadata/android/en-US/images/icon.png",
                "docs/brand/logo-official.png",
                "apps/desktop/public/fossify-calendar-icon.png",
            ]
        )
        == "docs/brand/logo-official.png"
    )
    assert (
        pick_icon_path(
            [
                "branding/assets/app-icon-512.svg",
                "branding/template/logo-mark.png",
            ],
            sizes={
                "branding/assets/app-icon-512.svg": 231,
                "branding/template/logo-mark.png": 500000,
            },
        )
        == "branding/template/logo-mark.png"
    )


def test_compose_shows_stars_watches_forks_views():
    body = compose_profile_readme(
        user={"login": "alice", "name": "Alice"},
        plans=[
            _plan(
                "alice/app",
                stars=3,
                forks=2,
                watches=4,
                traffic_views=17,
                icon="https://example.com/app.png",
                languages={"Python": 100},
            ),
            _plan(
                "alice/alice",
                stars=0,
                traffic_views=42,
                languages={"Python": 1},
            ),
        ],
        config={
            "about": "Hi",
            "principles": "P",
            "open_to": "O",
            "featured_columns": 7,
            "show_featured_stats": True,
            "show_profile_views": True,
            "max_featured_repos": 0,
            "banner_carries_identity": True,
        },
    )
    assert "./assets/octicons/star-16.svg" in body
    assert "./assets/octicons/eye-16.svg" in body
    assert "./assets/octicons/repo-forked-16.svg" in body
    assert "./assets/octicons/pulse-16.svg" in body
    assert "17" in body
    assert "Profile README views (14d Insights): 42" in body
    assert "traffic" not in body.lower()


def test_banner_svg_contains_name():
    svg = render_banner_svg("Alice", "Ship tools")
    assert "Alice" in svg
    assert "Ship tools" in svg
    assert "linearGradient" in svg


def test_needs_update():
    body = compose_profile_readme(
        user={"login": "bob"},
        plans=[],
        config={"about": "Hi", "principles": "P", "open_to": "O"},
    )
    assert needs_profile_update(None, body)
    assert not needs_profile_update(body, body)
