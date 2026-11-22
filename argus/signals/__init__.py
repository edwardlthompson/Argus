"""Signal collectors — pure-ish functions over GitHub API + repo metadata."""

from __future__ import annotations

from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord, SignalBundle
from argus.signals import (
    board,
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


def stamp_repo_raw(repo: RepoRecord, bundle: SignalBundle) -> None:
    """Stamp derived PR, issue, and CI metrics onto repo.raw for report views."""
    raw = dict(repo.raw or {})
    mom = bundle.momentum if isinstance(bundle.momentum, dict) else None
    prs_sig = bundle.prs if isinstance(bundle.prs, dict) else None
    ci_sig = bundle.ci if isinstance(bundle.ci, dict) else None

    if prs_sig is not None:
        pr_n = int(prs_sig.get("open_prs") or 0)
        raw["open_prs_count"] = pr_n
        if "dependabot_prs" in prs_sig or "release_prs" in prs_sig or "feature_prs" in prs_sig:
            raw["pr_dependabot"] = int(prs_sig.get("dependabot_prs") or 0)
            raw["pr_release"] = int(prs_sig.get("release_prs") or 0)
            raw["pr_feature"] = int(prs_sig.get("feature_prs") or 0)

    if mom is not None:
        total = int(mom.get("open_issues") or raw.get("open_issues_count") or 0)
        pr_n = int((prs_sig or {}).get("open_prs") or raw.get("open_prs_count") or 0)
        mom["open_issues_including_prs"] = total
        mom["open_issues"] = max(0, total - pr_n)
        raw["open_prs_count"] = pr_n
        raw["open_issues_only"] = mom["open_issues"]

    if ci_sig is not None:
        raw["ci_has_workflows"] = bool(ci_sig.get("has_workflows"))
        raw["ci_latest_conclusion"] = ci_sig.get("latest_conclusion")
        raw["ci_latest_failed"] = bool(ci_sig.get("latest_failed"))

    repo.raw = raw


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
        "board": board.collect,
    }
    for name, fn in collectors.items():
        try:
            setattr(bundle, name, fn(client, repo))
        except (GitHubError, KeyError, TypeError, ValueError):
            setattr(bundle, name, None)
    stamp_repo_raw(repo, bundle)
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
        board=data.get("board"),
    )
