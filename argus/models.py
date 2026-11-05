"""Shared domain types for Argus."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RepoStatus(StrEnum):
    SHIPPED = "shipped"
    ACTIVE = "active"
    EXPERIMENTAL = "experimental"
    PARKED = "parked"
    ARCHIVED = "archived"


class FixClass(StrEnum):
    AGENT = "agent"
    HUMAN = "human"
    AUTO_SAFE = "auto_safe"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Fix:
    id: str
    class_: FixClass
    title: str
    why: str
    applies_when: str
    phase: int
    depends_on: tuple[str, ...]
    confidence: Confidence
    auto_safe: bool
    gate: str | None
    agent_prompt: str | None
    human_steps: str | None
    resolution_ttl_days: int | None
    profiles: tuple[str, ...]


@dataclass
class RepoRecord:
    full_name: str
    owner: str
    name: str
    status: RepoStatus = RepoStatus.ACTIVE
    private: bool = False
    archived: bool = False
    fork: bool = False
    description: str | None = None
    default_branch: str = "main"
    html_url: str = ""
    permissions: dict[str, bool] = field(default_factory=dict)
    topics: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def can_write(self) -> bool:
        return bool(self.permissions.get("push") or self.permissions.get("admin"))


@dataclass
class SignalBundle:
    momentum: dict[str, Any] | None = None
    responsiveness: dict[str, Any] | None = None
    ci: dict[str, Any] | None = None
    deps: dict[str, Any] | None = None
    presentation: dict[str, Any] | None = None
    hygiene: dict[str, Any] | None = None
    security: dict[str, Any] | None = None
    lineage: dict[str, Any] | None = None
    prs: dict[str, Any] | None = None
    releases: dict[str, Any] | None = None

    def missing_categories(self) -> list[str]:
        # Core categories affect confidence; lineage/prs/releases are additive when present.
        cats = (
            "momentum",
            "responsiveness",
            "ci",
            "deps",
            "presentation",
            "hygiene",
            "security",
        )
        return [c for c in cats if getattr(self, c) is None]

    def as_dict(self) -> dict[str, Any]:
        return {
            "momentum": self.momentum,
            "responsiveness": self.responsiveness,
            "ci": self.ci,
            "deps": self.deps,
            "presentation": self.presentation,
            "hygiene": self.hygiene,
            "security": self.security,
            "lineage": self.lineage,
            "prs": self.prs,
            "releases": self.releases,
        }


@dataclass
class ScoreResult:
    attention: float
    confidence: Confidence
    category_scores: dict[str, float]
    notes: list[str] = field(default_factory=list)


@dataclass
class MatchedFix:
    fix: Fix
    reason: str = ""


@dataclass
class RepoPlan:
    repo: RepoRecord
    score: ScoreResult
    human_fixes: list[MatchedFix] = field(default_factory=list)
    agent_fixes: list[MatchedFix] = field(default_factory=list)
    auto_fixes: list[MatchedFix] = field(default_factory=list)
    report_only: bool = False
