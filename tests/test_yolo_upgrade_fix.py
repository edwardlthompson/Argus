"""Unit: soft-merge allowlist + markdown table normalizer."""

from __future__ import annotations

from argus.yolo_upgrade_fix import (
    SOFT_MERGE_ALLOWLIST,
    normalize_markdown_table_pipes,
    soft_merge_ok,
)


def test_soft_merge_allowlist_membership():
    assert "Template Upgrade Simulation" in SOFT_MERGE_ALLOWLIST
    assert soft_merge_ok(["Template Upgrade Simulation", "Validate Bootstrap Artifacts"])
    assert soft_merge_ok(["CI", "Validate Bootstrap Artifacts"])
    assert soft_merge_ok(["CI"])
    assert soft_merge_ok([])
    assert soft_merge_ok(["Conventional Commits PR Title", "Repo Hygiene"])


def test_soft_merge_blocks_security_and_product():
    assert not soft_merge_ok(["Security Scan"])
    assert not soft_merge_ok(["Trivy FS Scan"])
    assert not soft_merge_ok(["CodeQL"])
    assert soft_merge_ok(["CI", "Feature Gate"])
    assert not soft_merge_ok(["Template Upgrade Simulation", "Security Scan"])
    assert not soft_merge_ok(["Web - Lint, Test, Build"])
    assert not soft_merge_ok(["Android - assembleDebug"])
    assert not soft_merge_ok(["ADR Status"])
    assert not soft_merge_ok(["Scorecard analysis"])


def test_clear_blockers_steady_state_shape():
    from argus.yolo_clear_blockers import clear_open_upgrade_blockers

    assert callable(clear_open_upgrade_blockers)


def test_trivy_npm_overrides_apply():
    from argus.yolo_trivy_npm import CAPACITOR_PINS, NPM_OVERRIDES, _apply_pkg_json

    assert NPM_OVERRIDES["@xmldom/xmldom"] == "0.9.12"
    data = {
        "dependencies": {"@capacitor/android": "^8.4.2"},
        "overrides": {},
    }
    assert _apply_pkg_json(data) is True
    assert data["overrides"]["brace-expansion"] == "5.0.11"
    assert data["dependencies"]["@capacitor/android"] == CAPACITOR_PINS["@capacitor/android"]


def test_normalize_markdown_table_pipes():
    src = (
        "| A | B |\n"
        "|---|---|\n"
        "x|y\n"
        "| compact|row|\n"
    )
    out = normalize_markdown_table_pipes(src)
    assert "| x | y |" in out or "| x | y |" in out.replace("  ", " ")
    assert out.count("|") >= src.count("|")
    # idempotent-ish on already normalized header
    again = normalize_markdown_table_pipes(out)
    assert "| A | B |" in again
