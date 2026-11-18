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
        resolution_ttl_days=(int(raw["resolution_ttl_days"]) if raw.get("resolution_ttl_days") is not None else None),
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


def load_inbox(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "inbox.yaml")
    defaults = {
        "enabled": True,
        "controller_repo": "YOUR_LOGIN/argus-runner",
        "label_inbox": "argus-inbox",
        "label_security": "argus-security",
        "security_issues": False,
        "max_issues_per_run": 20,
    }
    if not path.exists():
        return defaults
    data = load_yaml(path)
    defaults.update(data if isinstance(data, dict) else {})
    return defaults


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


def _coalesce_dependabot_keys(
    block: dict[str, Any],
    src: dict[str, Any] | None,
    *,
    primary: str,
    alias: str,
    default_on: bool,
    default_levels: list[str],
) -> None:
    from argus.dependabot_policy import normalize_levels

    incoming = src or {}
    if primary in incoming:
        flag = bool(incoming[primary])
    elif alias in incoming:
        flag = bool(incoming[alias])
    else:
        flag = bool(block.get(primary, default_on))
    block[primary] = flag
    block[alias] = flag
    levels_src = incoming.get("dependabot_auto_merge_levels", block.get("dependabot_auto_merge_levels"))
    block["dependabot_auto_merge_levels"] = normalize_levels(levels_src, default_levels)


def load_safety(path: Path | None = None) -> dict[str, Any]:
    path = path or (CONFIG_DIR / "safety.yaml")
    yolo_defaults: dict[str, Any] = {
        "auto_merge_auto_safe": True,
        "auto_merge_dependabot": True,
        "auto_merge_dependabot_patch": True,  # alias of auto_merge_dependabot
        "dependabot_auto_merge_levels": ["patch", "minor", "major"],
        "auto_merge_upgrade_prs": True,
        "fix_upgrade_prs": True,
        "soft_merge_upgrade_noise": True,
        "clear_upgrade_blockers": True,
        "clear_upgrade_loops": 8,
        "clear_upgrade_sleep_s": 90,
        "merge_when_actions_billing": True,
        "skip_ci_when_actions_unavailable": True,
        "assume_actions_unavailable": False,
        "auto_rules_sync": True,
        "apply_api_handlers": True,
        "resolve_ci_when_actions_unavailable": True,
        "continuous_zero": True,
        "skip_profile": True,
        "sync_profile": True,
        "auto_dispatch_agents": True,
        "auto_merge_agent_prs": True,
        "max_auto_merges_per_day": 20,
        "close_stale_bot_prs_days": 0,
        "max_yolo_actions_per_run": 40,
        "second_pass_if_budget": True,
    }
    # Vanilla (apply_mode=normal): continuous-zero on explicit --apply only.
    # Merges stay human unless operator uses merge-upgrades --allow-unarmed.
    normal_defaults: dict[str, Any] = {
        "fix_upgrade_prs": True,
        "heal_upgrade_prs": True,
        "merge_upgrade_prs": False,
        "merge_dependabot": True,
        "merge_dependabot_patch": True,  # alias of merge_dependabot
        "dependabot_auto_merge_levels": ["patch", "minor"],
        "clear_upgrade_blockers": False,
        "yolo_handlers": True,
        "auto_rules_sync": True,
        "continuous_zero": True,
        "second_pass": True,
        "sync_profile": True,
        "quiet_digest_only": False,
    }
    # Authenticated REST core is 5000/hr; ~45–60 GETs per repo makes full-portfolio
    # multi-pass scans burn the hour — batch + reserve (see docs/RATE_LIMIT.md).
    github_api_defaults: dict[str, Any] = {
        "core_limit_hint": 5000,
        "reserve": 250,
        "min_interval_ms": 80,
        "max_interval_ms": 2000,
        "calls_per_repo_estimate": 50,
        "max_repos_per_batch": 6,
        "max_wait_seconds": 3700,
    }
    defaults: dict[str, Any] = {
        "max_auto_prs_per_run": 5,
        "max_auto_prs_per_owner": 3,
        "max_concurrent_agent_sessions": 1,
        "max_agent_prompt_chars": 12000,
        "max_gate_failures_before_pause": 2,
        "prefer_pull_requests": True,
        "never_delete_repos": True,
        "never_force_push": True,
        "attention_threshold_for_agents": 60,
        "apply_mode": "normal",
        "yolo": dict(yolo_defaults),
        "normal": dict(normal_defaults),
        "github_api": dict(github_api_defaults),
    }
    if not path.exists():
        return defaults
    data = load_yaml(path)
    yolo_in = data.pop("yolo", None) if isinstance(data, dict) else None
    normal_in = data.pop("normal", None) if isinstance(data, dict) else None
    api_in = data.pop("github_api", None) if isinstance(data, dict) else None
    defaults.update(data)
    merged_yolo = dict(yolo_defaults)
    if isinstance(yolo_in, dict):
        merged_yolo.update(yolo_in)
    _coalesce_dependabot_keys(
        merged_yolo,
        yolo_in if isinstance(yolo_in, dict) else None,
        primary="auto_merge_dependabot",
        alias="auto_merge_dependabot_patch",
        default_on=True,
        default_levels=["patch", "minor", "major"],
    )
    defaults["yolo"] = merged_yolo
    merged_normal = dict(normal_defaults)
    if isinstance(normal_in, dict):
        merged_normal.update(normal_in)
    _coalesce_dependabot_keys(
        merged_normal,
        normal_in if isinstance(normal_in, dict) else None,
        primary="merge_dependabot",
        alias="merge_dependabot_patch",
        default_on=True,
        default_levels=["patch", "minor"],
    )
    defaults["normal"] = merged_normal
    merged_api = dict(github_api_defaults)
    if isinstance(api_in, dict):
        merged_api.update(api_in)
    defaults["github_api"] = merged_api
    mode = str(defaults.get("apply_mode") or "normal").strip().lower()
    if mode not in ("normal", "yolo"):
        mode = "normal"
    defaults["apply_mode"] = mode
    return defaults
