"""Unit: hotspots + SVG infographic."""

from __future__ import annotations

from argus.health import write_health_artifacts
from argus.health_viz import compose_infographic_svg, hotspots_from_snapshot


def _snap(repos: list[dict]) -> dict:
    return {
        "totals": {
            "open_fixes": sum(
                len(r.get("auto", [])) + len(r.get("agent", [])) + len(r.get("human", []))
                for r in repos
            ),
            "mean_attention": 10.0,
        },
        "repos": repos,
    }


def test_hotspots_rank_fix_ids_and_repos():
    snap = _snap(
        [
            {
                "repo": "a/b",
                "attention": 80,
                "auto": ["SEC-CODEQL", "SEC-CODEQL"],
                "agent": [],
                "human": ["CI-LATEST-FAILED"],
            },
            {
                "repo": "c/d",
                "attention": 20,
                "auto": ["SEC-CODEQL"],
                "agent": [],
                "human": [],
            },
        ]
    )
    # fix counts: SEC-CODEQL appears 3 times if we count list entries as-is
    hot = hotspots_from_snapshot(snap)
    assert hot["by_fix_id"][0]["id"] == "SEC-CODEQL"
    assert hot["by_repo"][0]["repo"] == "a/b"


def test_infographic_svg_contains_before_after(tmp_path):
    before = _snap(
        [{"repo": "a/b", "attention": 50, "auto": ["X"], "agent": [], "human": []}]
    )
    after = _snap(
        [{"repo": "a/b", "attention": 10, "auto": [], "agent": [], "human": []}]
    )
    delta = {
        "delta_open_fixes": -1,
        "delta_mean_attention": -40.0,
        "totals_before": before["totals"],
        "totals_after": after["totals"],
    }
    svg = compose_infographic_svg(before, after, delta)
    assert "Before" in svg and "After" in svg
    assert "<svg" in svg
    paths = write_health_artifacts(
        before=before, after=after, delta=delta, dist_dir=tmp_path
    )
    assert (tmp_path / "health-infographic.svg").is_file()
    assert (tmp_path / "health-hotspots.json").is_file()
    assert "health_infographic_html" in paths
