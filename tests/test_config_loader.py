from __future__ import annotations

import pytest
import yaml

from argus.config_loader import ConfigError, _parse_fix, load_fixes, load_safety


def test_load_fixes_constitution():
    fixes = load_fixes()
    ids = {f.id for f in fixes}
    assert "HYGIENE-LICENSE" in ids
    assert "SEC-DEPENDABOT-ALERTS" in ids
    assert all(f.gate for f in fixes if f.class_.value in ("agent", "auto_safe"))


def test_load_safety_yolo_defaults():
    safety = load_safety()
    assert safety["apply_mode"] in ("normal", "yolo")
    assert safety["never_force_push"] is True
    assert safety["prefer_pull_requests"] is True
    yolo = safety["yolo"]
    assert yolo["auto_merge_auto_safe"] is True
    assert int(yolo["max_auto_merges_per_day"]) >= 1
    assert "close_stale_bot_prs_days" in yolo
    assert int(yolo.get("max_yolo_actions_per_run") or 0) >= 1
    api = safety["github_api"]
    assert api["core_limit_hint"] == 5000
    assert api["max_repos_per_batch"] == 6
    assert api["calls_per_repo_estimate"] == 50


def test_load_safety_yolo_merge(tmp_path):
    path = tmp_path / "safety.yaml"
    path.write_text(
        "apply_mode: yolo\n"
        "never_force_push: true\n"
        "yolo:\n"
        "  max_auto_merges_per_day: 7\n"
        "  close_stale_bot_prs_days: 14\n",
        encoding="utf-8",
    )
    safety = load_safety(path)
    assert safety["apply_mode"] == "yolo"
    assert safety["yolo"]["max_auto_merges_per_day"] == 7
    assert safety["yolo"]["close_stale_bot_prs_days"] == 14
    assert safety["yolo"]["auto_merge_dependabot_patch"] is True


def test_load_safety_invalid_mode_falls_back(tmp_path):
    path = tmp_path / "safety.yaml"
    path.write_text("apply_mode: reckless\n", encoding="utf-8")
    assert load_safety(path)["apply_mode"] == "normal"


def test_agent_fix_requires_gate(tmp_path):
    raw = {
        "id": "X",
        "class": "agent",
        "title": "t",
        "why": "w",
        "applies_when": "True",
        "phase": 1,
        "depends_on": [],
        "confidence": "high",
        "auto_safe": False,
        "profiles": ["generic"],
        "agent_prompt": "do it",
    }
    with pytest.raises(ConfigError):
        _parse_fix(raw)


def test_duplicate_ids_rejected(tmp_path):
    path = tmp_path / "fixes.yaml"
    path.write_text(
        yaml.safe_dump({
            "fixes": [
                {
                    "id": "A",
                    "class": "human",
                    "title": "t",
                    "why": "w",
                    "applies_when": "True",
                    "phase": 1,
                    "depends_on": [],
                    "confidence": "high",
                    "auto_safe": False,
                    "human_steps": "1. click",
                    "profiles": ["generic"],
                },
                {
                    "id": "A",
                    "class": "human",
                    "title": "t2",
                    "why": "w",
                    "applies_when": "True",
                    "phase": 1,
                    "depends_on": [],
                    "confidence": "high",
                    "auto_safe": False,
                    "human_steps": "1. click",
                    "profiles": ["generic"],
                },
            ]
        }),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_fixes(path)
