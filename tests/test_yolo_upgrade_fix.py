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


def test_soft_merge_blocks_security_and_product():
    assert not soft_merge_ok(["Security Scan"])
    assert not soft_merge_ok(["Trivy FS Scan"])
    assert not soft_merge_ok(["CodeQL"])
    assert not soft_merge_ok(["CI", "Feature Gate"])
    assert not soft_merge_ok(["Template Upgrade Simulation", "Security Scan"])
    assert not soft_merge_ok(["Web - Lint, Test, Build"])


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
