"""Release-freshness detection and PR planning (no network)."""

from __future__ import annotations

import yaml
from click.testing import CliRunner

from argus.cli import main as argus_main
from argus.config_loader import load_fixes, load_releases
from argus.models import FixClass
from argus.paths import CONFIG_DIR
from argus.release_detect import (
    bump_version_text,
    evaluate,
    extract_version,
    hot_triggers,
    match_platforms,
    next_version,
    skip_reason,
    use_authenticated_owner,
)
from argus.release_prep import plan_prep
from argus.release_report import compose_markdown, grandma_lines


def _cfg():
    return load_releases()


def test_fixes_catalogue_has_release_rows():
    fixes = {f.id: f for f in load_fixes()}
    assert fixes["RELEASE-PREP"].class_ == FixClass.AUTO_SAFE
    assert fixes["RELEASE-PREP"].gate
    assert fixes["RELEASE-IRREGULAR"].class_ == FixClass.AGENT
    assert fixes["RELEASE-IRREGULAR"].agent_prompt
    assert fixes["RELEASE-IRREGULAR"].gate


def test_skip_parked_fork_docs_and_empty_platforms():
    c = _cfg()
    parked = {"full_name": "o/r", "status": "parked", "owner": "o", "name": "r"}
    assert skip_reason(parked, ["python"], c) == "parked"
    forked = {"full_name": "o/r", "status": "active", "fork": True, "owner": "o", "name": "r"}
    assert skip_reason(forked, ["python"], c) == "fork"
    docs = {
        "full_name": "o/handbook", "status": "active", "owner": "o", "name": "handbook",
        "language": "Markdown", "topics": ["docs"],
    }
    assert skip_reason(docs, [], c) == "docs_only"
    profile = {"full_name": "o/o", "status": "active", "owner": "o", "name": "o"}
    assert skip_reason(profile, ["python"], c) == "profile_repo"
    empty = {"full_name": "o/lib", "status": "active", "owner": "o", "name": "lib"}
    assert skip_reason(empty, [], c) == "releases_not_applicable"


def test_match_platforms_from_paths():
    c = _cfg()
    assert "android" in match_platforms(["app/build.gradle.kts", "README.md"], c)
    assert "electron" in match_platforms(["electron/package.json", "electron-builder.yml"], c)
    assert "python" in match_platforms(["pyproject.toml"], c)
    assert "ios" in match_platforms(["App.xcodeproj/project.pbxproj"], c)
    assert match_platforms(["README.md", "docs/index.md"], c) == []


def test_stale_requires_commits_since():
    base = {
        "full_name": "o/app", "owner": "o", "name": "app", "status": "active",
        "platforms": ["python"], "has_release": True, "latest_tag": "v1.0.0",
        "days_since_release": 120, "ahead_by": 0, "has_tag_release_workflow": True,
        "asset_names": ["pkg-1.0.0-py3-none-any.whl"],
    }
    assert evaluate(base, _cfg())["stale"] is False
    assert evaluate({**base, "ahead_by": 3}, _cfg())["stale"] is True
    assert evaluate({**base, "ahead_by": 3}, _cfg())["needs_prep"] is True


def test_missing_release_and_apk_artifact():
    facts = {
        "full_name": "o/droid", "owner": "o", "name": "droid", "status": "active",
        "platforms": ["android"], "has_release": False, "has_tag_release_workflow": False,
        "ahead_by": 0, "asset_names": [],
    }
    out = evaluate(facts, _cfg())
    assert out["missing_release"] and out["needs_prep"]
    with_rel = {
        **facts, "has_release": True, "latest_tag": "v0.2.0",
        "days_since_release": 10, "asset_names": ["notes.txt"], "has_tag_release_workflow": True,
    }
    miss = evaluate(with_rel, _cfg())
    assert "android" in miss["missing_artifacts"]


def test_version_mismatch_and_next_tag():
    facts = {
        "full_name": "o/pkg", "owner": "o", "name": "pkg", "status": "active",
        "platforms": ["python"], "has_release": True, "latest_tag": "v1.2.3",
        "source_version": "1.2.4", "days_since_release": 1, "ahead_by": 0,
        "has_tag_release_workflow": True, "asset_names": ["x.whl"],
    }
    out = evaluate(facts, _cfg())
    assert out["version_mismatch"] is True
    assert next_version("v1.2.3", bump="patch") == "1.2.4"
    assert extract_version('version = "0.9.0"\n', "toml") == "0.9.0"
    assert 'version = "1.0.0"' in bump_version_text('version = "0.9.0"\n', "toml", "1.0.0")


def test_same_login_owner_uses_private_listing():
    assert use_authenticated_owner("edwardlthompson", "edwardlthompson", public_only=False)
    assert not use_authenticated_owner("edwardlthompson", "edwardlthompson", public_only=True)
    assert not use_authenticated_owner("other", "edwardlthompson", public_only=False)


def test_hot_triggers_ignore_tag_only():
    assert hot_triggers({"push": {"tags": ["v*"]}, "workflow_dispatch": None}) == []
    assert "push" in hot_triggers({"push": None, "pull_request": None})
    assert "pull_request" in hot_triggers(["push", "pull_request"])
    assert "schedule" in hot_triggers({"schedule": [{"cron": "0 0 * * *"}]})


def test_workflow_templates_are_tag_and_dispatch_only():
    for name in ("python.yml", "android.yml", "desktop.yml", "web.yml"):
        text = (CONFIG_DIR / "release_workflows" / name).read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        on = data.get("on") if isinstance(data, dict) else None
        if on is None and isinstance(data, dict):
            on = data.get(True)
        assert hot_triggers(on) == []
        assert "pull_request" not in yaml.dump(on)


def test_plan_omits_macos_on_private_desktop():
    row = {
        "full_name": "o/desk", "name": "desk", "private": True, "needs_prep": True, "irregular": False,
        "platforms": ["electron"], "missing": ["missing release"], "workflow_paths": [],
        "next_version": "0.1.1", "next_tag": "v0.1.1", "latest_tag": None,
        "electron_workdir": "electron",
    }
    plan = plan_prep(row, _cfg())
    wf = plan.files[".github/workflows/release-electron.yml"]
    assert "os: [windows-latest, ubuntu-latest]" in wf
    assert "macos-latest" not in wf.split("jobs:")[1]
    assert "10×" in plan.body
    pub = plan_prep({**row, "private": False}, _cfg())
    assert "macos-latest" in pub.files[".github/workflows/release-electron.yml"].split("jobs:")[1]
    assert "git tag -a v0.1.1" in plan.body
    on = yaml.safe_load(wf).get("on") or yaml.safe_load(wf).get(True)
    assert hot_triggers(on) == []


def test_irregular_ios_does_not_invent_workflow():
    row = {
        "full_name": "o/ios", "name": "ios", "needs_prep": True, "irregular": True,
        "platforms": ["ios"], "missing": ["missing release"],
    }
    plan = plan_prep(row, _cfg())
    assert plan.irregular is True
    assert plan.files == {}


def test_grandma_and_minutes_section():
    rows = [
        {
            "full_name": "o/app", "platforms": ["python"], "latest_tag": None, "needs_prep": True,
            "missing": ["missing release"], "visibility": "private", "private": True,
            "workflows": [{"path": ".github/workflows/ci.yml", "hot": ["push", "pull_request"]}],
        },
        {
            "full_name": "o/ok", "needs_prep": False, "visibility": "public",
            "workflows": [{"path": ".github/workflows/release.yml", "hot": []}],
        },
    ]
    md = compose_markdown(rows, dry_run=True, listing="user_public")
    assert "o/app" in md and "missing release" in md
    assert "Actions minutes" in md
    assert ".github/workflows/ci.yml" in md
    assert "private (billed)" in md
    assert "1 private repo(s)" in md
    assert "classic `repo` PAT" in md
    assert grandma_lines([rows[0]])[0].startswith("o/app:")


def test_cli_help_mentions_open_prs():
    result = CliRunner().invoke(argus_main, ["releases", "--help"])
    assert result.exit_code == 0
    assert "--open-prs" in result.output
    assert "--dry-run" in result.output


def test_existing_fixture_plans_do_not_gain_release_fixes():
    from argus.pipeline import build_plans_from_fixtures
    from tests.conftest import load_fixture

    plan = build_plans_from_fixtures([load_fixture("docs_only.json")])[0]
    ids = {m.fix.id for m in plan.auto_fixes + plan.agent_fixes + plan.human_fixes}
    assert "RELEASE-PREP" not in ids
    assert "RELEASE-IRREGULAR" not in ids
