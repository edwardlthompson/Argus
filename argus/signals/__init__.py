"""Signal collectors — pure-ish functions over GitHub API + repo metadata."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord, SignalBundle
from argus.signals import (
    ci,
    contract,
    deps,
    hygiene,
    lineage,
    momentum,
    orphans,
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
        "orphans": orphans.collect,
        "contract": contract.collect,
    }
    for name, fn in collectors.items():
        try:
            setattr(bundle, name, fn(client, repo))
        except (GitHubError, KeyError, TypeError, ValueError):
            setattr(bundle, name, None)
    # GitHub open_issues_count includes PRs — stamp Issues-only for reports/fixes.
    mom = bundle.momentum if isinstance(bundle.momentum, dict) else None
    prs_sig = bundle.prs if isinstance(bundle.prs, dict) else None
    if mom is not None:
        total = int(mom.get("open_issues") or (repo.raw or {}).get("open_issues_count") or 0)
        pr_n = int((prs_sig or {}).get("open_prs") or 0)
        mom["open_issues_including_prs"] = total
        mom["open_issues"] = max(0, total - pr_n)
        raw = dict(repo.raw or {})
        raw["open_prs_count"] = pr_n
        raw["open_issues_only"] = mom["open_issues"]
        repo.raw = raw
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
        orphans=data.get("orphans"),
        contract=data.get("contract"),
    )
