"""Signal collectors — pure-ish functions over GitHub API + repo metadata."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord, SignalBundle
from argus.signals import (
    ci,
    deps,
    hygiene,
    lineage,
    momentum,
    presentation,
    prs,
    releases,
    responsiveness,
    security,
    traffic,
)


def collect_signals(client: GitHubClient, repo: RepoRecord) -> SignalBundle:
    """Collect all signal categories; missing categories remain None on failure."""
    bundle = SignalBundle()
    collectors = {
        "momentum": momentum.collect,
        "responsiveness": responsiveness.collect,
        "ci": ci.collect,
        "deps": deps.collect,
        "presentation": presentation.collect,
        "hygiene": hygiene.collect,
        "security": security.collect,
        "lineage": lineage.collect,
        "prs": prs.collect,
        "releases": releases.collect,
        "traffic": traffic.collect,
    }
    for name, fn in collectors.items():
        try:
            setattr(bundle, name, fn(client, repo))
        except (GitHubError, KeyError, TypeError, ValueError):
            setattr(bundle, name, None)
    return bundle


def fixture_bundle(data: dict[str, Any]) -> SignalBundle:
    return SignalBundle(
        momentum=data.get("momentum"),
        responsiveness=data.get("responsiveness"),
        ci=data.get("ci"),
        deps=data.get("deps"),
        presentation=data.get("presentation"),
        hygiene=data.get("hygiene"),
        security=data.get("security"),
        lineage=data.get("lineage"),
        prs=data.get("prs"),
        releases=data.get("releases"),
        traffic=data.get("traffic"),
    )
