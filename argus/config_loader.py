"""Load and validate Argus YAML configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from argus.models import Confidence, Fix, FixClass, RepoStatus
from argus.paths import CONFIG_DIR


class ConfigError(ValueError):
    """Raised when configuration is invalid."""


REQUIRED_FIX_FIELDS = (
    "id",
    "class",
    "title",
    "why",
    "applies_when",
    "phase",
    "depends_on",
    "confidence",
    "auto_safe",
    "profiles",
)


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if data is not None else {}


def _parse_fix(raw: dict[str, Any]) -> Fix:
    missing = [f for f in REQUIRED_FIX_FIELDS if f not in raw]
    if missing:
        raise ConfigError(f"Fix missing fields {missing}: {raw.get('id', '<unknown>')}")

    class_ = FixClass(raw["class"])
    gate = raw.get("gate")
    agent_prompt = raw.get("agent_prompt")
    human_steps = raw.get("human_steps")

    if class_ in (FixClass.AGENT, FixClass.AUTO_SAFE) and not gate:
        raise ConfigError(f"Fix {raw['id']}: agent/auto_safe fixes require a gate")
    if class_ == FixClass.AGENT and not agent_prompt:
        raise ConfigError(f"Fix {raw['id']}: agent class requires agent_prompt")
    if class_ == FixClass.HUMAN and not human_steps:
        raise ConfigError(f"Fix {raw['id']}: human class requires human_steps")

    phase = int(raw["phase"])
    if phase not in (1, 2, 3, 4):
        raise ConfigError(f"Fix {raw['id']}: phase must be 1..4, got {phase}")

    auto_safe = bool(raw["auto_safe"])
    if class_ == FixClass.AUTO_SAFE and not auto_safe:
        raise ConfigError(f"Fix {raw['id']}: class auto_safe requires auto_safe: true")
    if auto_safe and class_ != FixClass.AUTO_SAFE:
        raise ConfigError(f"Fix {raw['id']}: auto_safe true requires class auto_safe")

    return Fix(
        id=str(raw["id"]),
        class_=class_,
        title=str(raw["title"]),
        why=str(raw["why"]),
        applies_when=str(raw["applies_when"]),
        phase=phase,
        depends_on=tuple(str(x) for x in (raw.get("depends_on") or [])),
        confidence=Confidence(raw["confidence"]),
        auto_safe=auto_safe,
        gate=str(gate) if gate else None,
        agent_prompt=str(agent_prompt) if agent_prompt else None,
        human_steps=str(human_steps) if human_steps else None,
        resolution_ttl_days=(
            int(raw["resolution_ttl_days"]) if raw.get("resolution_ttl_days") is not None else None
        ),
        profiles=tuple(str(p) for p in raw["profiles"]),
    )


def load_fixes(path: Path | None = None) -> list[Fix]:
    """Load fixes from fixes.yaml plus optional config/fixes/*.yaml shards (<300 lines each)."""
    paths: list[Path] = []
    if path is not None:
        paths.append(path)
    else:
        main = CONFIG_DIR / "fixes.yaml"
        paths.append(main)
        shard_dir = CONFIG_DIR / "fixes"
        if shard_dir.is_dir():
            paths.extend(sorted(shard_dir.glob("*.yaml")))

    items: list[dict[str, Any]] = []
    for p in paths:
        data = load_yaml(p)
        chunk = data.get("fixes") if isinstance(data, dict) else data
        if chunk is None:
            continue
        if not isinstance(chunk, list):
            raise ConfigError(f"{p} must contain a 'fixes' list")
        items.extend(chunk)

    fixes = [_parse_fix(item) for item in items]
    ids = [f.id for f in fixes]
    if len(ids) != len(set(ids)):
        raise ConfigError("Duplicate fix ids in fixes catalogue")
    known = set(ids)
    for fix in fixes:
        for dep in fix.depends_on:
            if dep not in known:
                raise ConfigError(f"Fix {fix.id} depends_on unknown id: {dep}")
    return fixes


def load_rubric(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "rubric.yaml")
    data = load_yaml(path)
    if "weights" not in data:
        raise ConfigError("rubric.yaml requires 'weights'")
    return data


def load_status(path: Path | None = None) -> dict[str, RepoStatus]:
    path = path or (CONFIG_DIR / "status.yaml")
    data = load_yaml(path)
    repos = data.get("repos", {}) if isinstance(data, dict) else {}
    out: dict[str, RepoStatus] = {}
    for name, meta in repos.items():
        if isinstance(meta, str):
            out[name] = RepoStatus(meta)
        elif isinstance(meta, dict) and "status" in meta:
            out[name] = RepoStatus(meta["status"])
        else:
            raise ConfigError(f"Invalid status entry for {name}")
    return out


def load_notifications(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "notifications.yaml")
    return load_yaml(path)


def load_profile(name: str = "generic", path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "profiles" / f"{name}.yaml")
    return load_yaml(path)


def load_allowlist(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "allowlist.yaml")
    if not path.exists():
        return {"mode": "owner_only", "allow": [], "deny": []}
    data = load_yaml(path)
    return {
        "mode": data.get("mode", "owner_only"),
        "allow": list(data.get("allow") or []),
        "deny": list(data.get("deny") or []),
    }


def load_safety(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "safety.yaml")
    defaults = {
        "max_auto_prs_per_run": 5,
        "max_concurrent_agent_sessions": 1,
        "max_agent_prompt_chars": 12000,
        "max_gate_failures_before_pause": 2,
        "prefer_pull_requests": True,
        "never_delete_repos": True,
        "never_force_push": True,
    }
    if not path.exists():
        return defaults
    data = load_yaml(path)
    defaults.update(data)
    return defaults
