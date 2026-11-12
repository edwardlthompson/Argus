"""Patterned Issue auto-close predicates."""

from __future__ import annotations

from argus.yolo_issues import is_patterned_auto_close


def test_argus_auto_label_closes():
    assert is_patterned_auto_close(
        {"number": 1, "title": "whatever", "labels": [{"name": "argus-auto"}], "user": {"login": "alice"}}
    )


def test_digest_title_closes():
    assert is_patterned_auto_close(
        {
            "number": 2,
            "title": "yolo-digest 2026-11-11",
            "labels": [],
            "user": {"login": "edwardlthompson"},
        }
    )


def test_dependabot_bump_closes():
    assert is_patterned_auto_close(
        {
            "number": 3,
            "title": "Bump requests from 2.0 to 2.1",
            "labels": [],
            "user": {"login": "dependabot[bot]"},
        }
    )


def test_human_product_bug_not_auto_close():
    assert not is_patterned_auto_close(
        {
            "number": 4,
            "title": "Crash on login when offline",
            "labels": [{"name": "bug"}],
            "user": {"login": "alice"},
        }
    )


def test_pull_request_never_auto_close():
    assert not is_patterned_auto_close(
        {
            "number": 5,
            "title": "chore(argus): something",
            "pull_request": {"url": "https://example"},
            "user": {"login": "dependabot[bot]"},
        }
    )
