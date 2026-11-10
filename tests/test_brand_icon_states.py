from __future__ import annotations

from argus.signals.hygiene import _REJECT_BASE, classify_brand_icon


def test_owned_when_unique_png():
    assert (
        classify_brand_icon(
            path="branding/assets/app-icon-512.png",
            size=1200,
            sha256="a" * 64,
            parent_hashes=set(),
            stub_svg_max=400,
        )
        == "owned"
    )


def test_inherited_matches_parent_hash():
    h = "b" * 64
    assert (
        classify_brand_icon(
            path="branding/assets/app-icon-512.png",
            size=1200,
            sha256=h,
            parent_hashes={h},
            stub_svg_max=400,
        )
        == "inherited"
    )


def test_missing_and_placeholder():
    assert (
        classify_brand_icon(
            path=None, size=0, sha256=None, parent_hashes=set(), stub_svg_max=400
        )
        == "missing"
    )
    assert (
        classify_brand_icon(
            path="branding/assets/app-icon-512.png",
            size=100,
            sha256="c" * 64,
            parent_hashes=set(),
            stub_svg_max=400,
        )
        == "placeholder"
    )
    assert (
        classify_brand_icon(
            path="branding/assets/mark.svg",
            size=200,
            sha256="d" * 64,
            parent_hashes=set(),
            stub_svg_max=400,
        )
        == "placeholder"
    )


def test_reject_basenames():
    for base in ("favicon", "social-preview", "splash", "wordmark"):
        assert base in _REJECT_BASE
        assert (
            classify_brand_icon(
                path=f"assets/{base}.png",
                size=2000,
                sha256="e" * 64,
                parent_hashes=set(),
                stub_svg_max=400,
            )
            == "placeholder"
        )
