"""Deterministic scoring from signals + rubric.yaml. No LLMs."""

from __future__ import annotations

from typing import Any

from argus.models import Confidence, RepoStatus, ScoreResult, SignalBundle


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))

def _cat_score(name: str, data: dict[str, Any] | None, rubric: dict[str, Any]) -> float | None:
    if data is None:
        return None
    rules = rubric.get("category_rules", {}).get(name, {})
    score = float(rules.get("base", 50))

    if name == "momentum":
        days = data.get("days_since_push")
        if days is None:
            score = 40
        elif days > 180:
            score = 90
        elif days > 90:
            score = 70
        elif days > 30:
            score = 40
        else:
            score = 15
    elif name == "responsiveness":
        stale = int(data.get("stale_issues_90d") or 0)
        score = _clamp(20 + stale * 15)
    elif name == "ci":
        score = 10 if data.get("has_workflows") else 85
        if data.get("latest_failed"):
            score = _clamp(score + 40)
        days = data.get("days_since_run")
        if data.get("has_workflows") and days is not None and days > 90:
            score = _clamp(score + 20)
    elif name == "deps":
        score = 20
        if not data.get("vulnerability_alerts_enabled"):
            score += 40
        if not data.get("has_dependabot_config"):
            score += 25
        score += min(40, int(data.get("open_dependabot_alerts") or 0) * 10)
    elif name == "presentation":
        score = 10
        if int(data.get("description_len") or 0) == 0:
            score += 35
        elif int(data.get("description_len") or 0) > 120:
            score += 20
        if int(data.get("specific_topic_count") or 0) < 3:
            score += 25
        if not data.get("has_readme"):
            score += 30
    elif name == "hygiene":
        score = 5
        for key, weight in (
            ("license_file", 25),
            ("security_md", 20),
            ("contributing_md", 15),
            ("code_of_conduct_md", 10),
            ("gitattributes", 15),
        ):
            if not data.get(key):
                score += weight
        for key, weight in (("codeowners", 10), ("gitignore", 5)):
            if key in data and not data.get(key):
                score += weight
        if "license_spdx" in data and data.get("license_spdx") in (None, "NOASSERTION", ""):
            score = _clamp(score + 8)
        if "stale_branch_count" in data:
            score = _clamp(score + min(15, int(data.get("stale_branch_count") or 0) * 3))
        if data.get("branch_protection") is False:
            score = _clamp(score + 10)
        runs = data.get("actions_runs_30d")
        if isinstance(runs, int) and runs > 500:
            score = _clamp(score + 5)
    elif name == "security":
        score = 10 if data.get("secret_scanning_enabled") else 70
        if not data.get("codeql_likely"):
            score += 15
    elif name == "lineage":
        score = 5
        if data.get("is_template_child"):
            if data.get("version_behind"):
                score += 50
            score += min(40, len(data.get("missing_lineage_files") or []) * 10)
        else:
            score = 0
    elif name == "prs":
        score = _clamp(10 + int(data.get("stale_prs_30d") or 0) * 20)
    elif name == "releases":
        score = 5
        if not data.get("has_release"):
            score = 35

    return _clamp(score)

def score_repo(
    signals: SignalBundle,
    rubric: dict[str, Any],
    status: RepoStatus,
) -> ScoreResult:
    weights: dict[str, float] = {k: float(v) for k, v in rubric.get("weights", {}).items()}
    status_cfg = rubric.get("status_multipliers", {}).get(status.value, {})
    allowed = status_cfg.get("categories")
    multiplier = float(status_cfg.get("multiplier", 1.0))

    category_scores: dict[str, float] = {}
    notes: list[str] = []
    missing = signals.missing_categories()

    for name, _weight in weights.items():
        if allowed is not None and name not in allowed:
            continue
        data = getattr(signals, name)
        value = _cat_score(name, data, rubric)
        if value is None:
            missing.append(name)
            continue
        category_scores[name] = value

    if not category_scores:
        return ScoreResult(attention=0.0, confidence=Confidence.LOW, category_scores={}, notes=["no signals"])

    # Weighted average over available categories
    total_w = sum(weights.get(n, 1.0) for n in category_scores)
    attention = sum(category_scores[n] * weights.get(n, 1.0) for n in category_scores) / max(total_w, 1e-9)
    attention = _clamp(attention * multiplier)

    unique_missing = sorted(set(missing))
    if len(unique_missing) > 2:
        confidence = Confidence.LOW
        notes.append(f"missing categories: {', '.join(unique_missing)}")
    elif unique_missing:
        confidence = Confidence.MEDIUM
        notes.append(f"missing categories: {', '.join(unique_missing)}")
    else:
        confidence = Confidence.HIGH

    if status in (RepoStatus.PARKED, RepoStatus.ARCHIVED):
        notes.append("hygiene/security-only scoring for parked/archived")

    return ScoreResult(
        attention=round(attention, 1),
        confidence=confidence,
        category_scores={k: round(v, 1) for k, v in category_scores.items()},
        notes=notes,
    )
