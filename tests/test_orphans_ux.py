from __future__ import annotations

from pathlib import Path

from argus.signals.orphans import should_skip_path
from argus.ux.loader import BASE_EXCLUDES, SKIP_PREFIXES, _excluded, load_rules


def test_orphans_skip_examples_and_cursor():
    assert should_skip_path("examples/demo/App.tsx")
    assert should_skip_path(".cursor/rules/foo.mdc")
    assert not should_skip_path("src/App.tsx")


def test_base_excludes_have_coverage():
    assert "*.md" in BASE_EXCLUDES
    assert "*.mdc" in BASE_EXCLUDES
    assert "LICENSE*" in BASE_EXCLUDES
    assert _excluded("README.md")
    assert _excluded("docs/notes.md")
    assert _excluded(".cursor/rules/x.mdc") or _excluded("rules/x.mdc")
    assert _excluded("LICENSE")
    assert _excluded("LICENSE.txt")
    assert _excluded("CHANGELOG.md")
    assert not _excluded("src/app.py")


def test_skip_prefixes():
    assert ".cursor/" in SKIP_PREFIXES
    assert _excluded(".cursor/hooks.json")
    assert _excluded("examples/web/index.html")
    assert not _excluded("src/main.py")


def test_load_rules_empty_without_fixtures(tmp_path: Path):
    assert load_rules("missing-stack", rules_dir=tmp_path / "nope") == []
