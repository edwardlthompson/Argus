"""UX rule rollout: observe → soft → enforce with fp_rate promote/demote."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from argus.paths import CONFIG_DIR, STATE_DIR, ensure_runtime_dirs

STAGES = ("observe", "soft", "enforce")


def _cfg_path() -> Path:
    return CONFIG_DIR / "ux_rollout.yaml"


def _state_path() -> Path:
    return STATE_DIR / "ux_rollout.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or _cfg_path()
    if not p.is_file():
        return {
            "default_stage": "observe",
            "promote_fp_rate_max": 0.05,
            "demote_fp_rate_min": 0.20,
            "min_samples_for_promote": 10,
            "min_samples_for_demote": 5,
        }
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def load_state(path: Path | None = None) -> dict[str, Any]:
    ensure_runtime_dirs()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = path or _state_path()
    if not p.is_file():
        return {"version": 1, "rules": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "rules": {}}


def save_state(state: dict[str, Any], path: Path | None = None) -> Path:
    ensure_runtime_dirs()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = path or _state_path()
    p.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return p


def rule_entry(state: dict[str, Any], rule_id: str, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    rules = state.setdefault("rules", {})
    if rule_id not in rules:
        rules[rule_id] = {
            "stage": str(cfg.get("default_stage") or "observe"),
            "true_positives": 0,
            "false_positives": 0,
        }
    return rules[rule_id]


def stage_for(rule_id: str, *, state: dict[str, Any] | None = None, cfg: dict[str, Any] | None = None) -> str:
    st = state if state is not None else load_state()
    entry = rule_entry(st, rule_id, cfg)
    stage = str(entry.get("stage") or "observe")
    return stage if stage in STAGES else "observe"


def fp_rate(entry: dict[str, Any]) -> float | None:
    tp = int(entry.get("true_positives") or 0)
    fp = int(entry.get("false_positives") or 0)
    total = tp + fp
    if total == 0:
        return None
    return fp / total


def record_outcome(
    rule_id: str,
    *,
    false_positive: bool,
    state: dict[str, Any] | None = None,
    cfg: dict[str, Any] | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    cfg = cfg or load_config()
    st = state if state is not None else load_state()
    entry = rule_entry(st, rule_id, cfg)
    if false_positive:
        entry["false_positives"] = int(entry.get("false_positives") or 0) + 1
    else:
        entry["true_positives"] = int(entry.get("true_positives") or 0) + 1
    maybe_promote_demote(rule_id, state=st, cfg=cfg)
    if persist:
        save_state(st)
    return entry


def maybe_promote_demote(
    rule_id: str,
    *,
    state: dict[str, Any],
    cfg: dict[str, Any] | None = None,
) -> str:
    cfg = cfg or load_config()
    entry = rule_entry(state, rule_id, cfg)
    stage = str(entry.get("stage") or "observe")
    rate = fp_rate(entry)
    if rate is None:
        return stage
    samples = int(entry.get("true_positives") or 0) + int(entry.get("false_positives") or 0)
    promote_max = float(cfg.get("promote_fp_rate_max") or 0.05)
    demote_min = float(cfg.get("demote_fp_rate_min") or 0.20)
    min_up = int(cfg.get("min_samples_for_promote") or 10)
    min_down = int(cfg.get("min_samples_for_demote") or 5)
    idx = STAGES.index(stage) if stage in STAGES else 0
    if samples >= min_up and rate <= promote_max and idx < len(STAGES) - 1:
        entry["stage"] = STAGES[idx + 1]
    elif samples >= min_down and rate >= demote_min and idx > 0:
        entry["stage"] = STAGES[idx - 1]
    return str(entry["stage"])


def actionable(rule_id: str, *, state: dict[str, Any] | None = None) -> bool:
    """True when findings may feed triage / gated apply (enforce only)."""
    return stage_for(rule_id, state=state) == "enforce"


def reportable(rule_id: str, *, state: dict[str, Any] | None = None) -> bool:
    """Soft + enforce surface findings; observe stays silent except counters."""
    return stage_for(rule_id, state=state) in ("soft", "enforce")
