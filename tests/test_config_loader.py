from __future__ import annotations

import pytest
import yaml

from argus.config_loader import ConfigError, _parse_fix, load_fixes


def test_load_fixes_constitution():
    fixes = load_fixes()
    ids = {f.id for f in fixes}
    assert "HYGIENE-LICENSE" in ids
    assert "SEC-DEPENDABOT-ALERTS" in ids
    assert all(f.gate for f in fixes if f.class_.value in ("agent", "auto_safe"))


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
