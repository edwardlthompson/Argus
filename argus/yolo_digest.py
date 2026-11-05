"""Private-runner YOLO digest Issue for leftovers that stay human-judged."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from argus.apply_history import _put_file, _resolve_controller
from argus.config_loader import load_inbox
from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoPlan

DIGEST_LABEL = "argus-yolo-digest"
JUDGMENT_IDS = frozenset({
    "CI-LATEST-FAILED",
    "HUMAN-PARK-INACTIVE",
    "HUMAN-ARCHIVE-JUDGMENT",
})


@dataclass
class DigestResult:
    action: str = "skipped"
    url: str | None = None
    items: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def collect_judgment_items(plans: list[RepoPlan], extra: list[str] | None = None) -> list[str]:
    items: list[str] = []
    for plan in plans:
        for m in (*plan.human_fixes, *plan.agent_fixes):
            if m.fix.id in JUDGMENT_IDS or m.fix.id == "PR-STALE":
                items.append(f"- `{plan.repo.full_name}` · `{m.fix.id}` — {m.fix.title}")
    for line in extra or []:
        if line not in items:
            items.append(line)
    return items


def upsert_yolo_digest(
    client: GitHubClient,
    items: list[str],
    *,
    dry_run: bool = False,
) -> DigestResult:
    result = DigestResult(items=items)
    inbox = load_inbox()
    if not inbox.get("enabled", True):
        return result
    controller = _resolve_controller(client, inbox)
    if not controller:
        return result
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    title = f"yolo-digest {day}"
    body = "\n".join([
        f"# Argus YOLO digest — {day}",
        "",
        "Items below need human judgment (YOLO will not auto-archive, invent CI patches, "
        "or close human-authored PRs).",
        "",
        *(items or ["_Nothing left that needs you today._"]),
        "",
    ])
    if dry_run:
        result.action = "dry_run"
        return result
    owner, name = controller.split("/", 1)
    try:
        try:
            client.post(
                f"/repos/{owner}/{name}/labels",
                allow_write=True,
                json={
                    "name": DIGEST_LABEL,
                    "color": "0E8A16",
                    "description": "Argus YOLO leftovers",
                },
            )
        except GitHubError:
            pass
        open_issues = client.get(
            f"/repos/{owner}/{name}/issues",
            params={"state": "open", "labels": DIGEST_LABEL, "per_page": 10},
        )
        existing = None
        if isinstance(open_issues, list):
            for iss in open_issues:
                if str(iss.get("title") or "").startswith("yolo-digest"):
                    existing = iss
                    break
        if existing and not items:
            client.patch(
                f"/repos/{owner}/{name}/issues/{existing['number']}",
                allow_write=True,
                json={"state": "closed", "body": body},
            )
            result.action = "closed"
            result.url = existing.get("html_url")
            return result
        if existing:
            client.patch(
                f"/repos/{owner}/{name}/issues/{existing['number']}",
                allow_write=True,
                json={"title": title, "body": body, "labels": [DIGEST_LABEL]},
            )
            result.action = "updated"
            result.url = existing.get("html_url")
            return result
        if not items:
            result.action = "noop"
            return result
        created = client.post(
            f"/repos/{owner}/{name}/issues",
            allow_write=True,
            json={"title": title, "body": body, "labels": [DIGEST_LABEL]},
        )
        result.action = "opened"
        result.url = created.get("html_url") if isinstance(created, dict) else None
    except GitHubError as exc:
        result.action = "error"
        result.errors.append(str(exc))
    return result


def sync_report_files(
    client: GitHubClient,
    *,
    html: str,
    markdown: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Push dated shareable reports to private controller argus-history/reports/."""
    inbox = load_inbox()
    controller = _resolve_controller(client, inbox)
    out: dict[str, Any] = {"action": "skipped"}
    if not controller or not inbox.get("enabled", True):
        return out
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    if dry_run:
        out["action"] = "dry_run"
        out["detail"] = f"would_write:{controller}/argus-history/reports/{day}.*"
        return out
    try:
        out["html_url"] = _put_file(
            client, controller, f"argus-history/reports/{day}.html", html,
            f"chore(argus): portfolio report {day}.html",
        )
        out["md_url"] = _put_file(
            client, controller, f"argus-history/reports/{day}.md", markdown,
            f"chore(argus): portfolio report {day}.md",
        )
        out["action"] = "updated"
    except GitHubError as exc:
        out["action"] = "error"
        out["errors"] = [str(exc)]
    return out
