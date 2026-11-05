"""Notifications: email, Discord, Telegram, generic webhook. Silent by default."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from argus.config_loader import load_inbox, load_notifications
from argus.models import RepoPlan
from argus.notify_channels import dispatch_message
from argus.notify_log import append_notification_log


@dataclass
class NotifyResult:
    sent: list[str]
    skipped: str | None = None


def _merge_env(cfg: dict[str, Any]) -> dict[str, Any]:
    """Overlay secrets from environment onto notifications config."""
    out = dict(cfg)
    discord = dict(out.get("discord") or {})
    if os.environ.get("ARGUS_DISCORD_WEBHOOK"):
        discord["enabled"] = True
        discord["webhook_url"] = os.environ["ARGUS_DISCORD_WEBHOOK"]
    out["discord"] = discord
    telegram = dict(out.get("telegram") or {})
    if os.environ.get("ARGUS_TELEGRAM_BOT_TOKEN") and os.environ.get("ARGUS_TELEGRAM_CHAT_ID"):
        telegram["enabled"] = True
        telegram["bot_token"] = os.environ["ARGUS_TELEGRAM_BOT_TOKEN"]
        telegram["chat_id"] = os.environ["ARGUS_TELEGRAM_CHAT_ID"]
    out["telegram"] = telegram
    webhook = dict(out.get("webhook") or {})
    if os.environ.get("ARGUS_WEBHOOK_URL"):
        webhook["enabled"] = True
        webhook["url"] = os.environ["ARGUS_WEBHOOK_URL"]
    out["webhook"] = webhook
    return out


def should_notify(plans: list[RepoPlan], config: dict[str, Any] | None = None) -> bool:
    cfg = _merge_env(config or load_notifications())
    human = sum(len(p.human_fixes) for p in plans)
    if human > 0 and cfg.get("notify_on_human_work", True):
        return True
    if cfg.get("notify_on_critical_security", True):
        for plan in plans:
            sec = plan.score.category_scores.get("security", 0)
            if sec >= float(cfg.get("critical_security_threshold", 80)):
                return True
    return False


def control_plane_urls() -> dict[str, str | None]:
    """Deep links for Issues inbox and Actions (never CVE lists)."""
    inbox_cfg = load_inbox()
    controller = str(inbox_cfg.get("controller_repo") or "edwardlthompson/Argus")
    label = str(inbox_cfg.get("label_inbox") or "argus-inbox")
    base = f"https://github.com/{controller}"
    inbox_url = f"{base}/issues?q=is%3Aissue+is%3Aopen+label%3A{label}"
    run_url = os.environ.get("ARGUS_RUN_URL") or os.environ.get("GITHUB_RUN_URL")
    if not run_url:
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        repo = os.environ.get("GITHUB_REPOSITORY", controller)
        run_id = os.environ.get("GITHUB_RUN_ID")
        run_url = (
            f"{server}/{repo}/actions/runs/{run_id}" if run_id else f"{base}/actions"
        )
    return {
        "inbox_url": inbox_url,
        "run_url": run_url,
        "status_url": os.environ.get("ARGUS_REPORT_URL"),
    }


def build_summary(
    plans: list[RepoPlan],
    report_url: str | None = None,
    *,
    inbox_url: str | None = None,
    run_url: str | None = None,
) -> str:
    """Safe digest: counts + deep links. No CVE titles or per-repo security gaps."""
    human = sum(len(p.human_fixes) for p in plans)
    urls = control_plane_urls()
    inbox = inbox_url or urls["inbox_url"]
    run = run_url or urls["run_url"]
    status = report_url or urls.get("status_url")
    if human == 0:
        return "Argus finished with no human tasks."
    noun = "task" if human == 1 else "tasks"
    lines = [f"Argus needs you for {human} small {noun}."]
    if inbox:
        lines.append(f"Inbox: {inbox}")
    if run:
        lines.append(f"Actions (private artifact): {run}")
    if status:
        lines.append(f"Status: {status}")
    return "\n".join(lines)


def send_error_notification(message: str, *, report_url: str | None = None) -> NotifyResult:
    cfg = _merge_env(load_notifications())
    if not cfg.get("notify_on_run_error", True):
        return NotifyResult(sent=[], skipped="errors_disabled")
    text = f"Argus run failed: {message}"
    urls = control_plane_urls()
    if urls.get("run_url"):
        text += f"\nActions: {urls['run_url']}"
    if report_url:
        text += f"\nStatus: {report_url}"
    return NotifyResult(sent=dispatch_message(text, cfg, report_url=report_url))


def send_notifications(
    plans: list[RepoPlan],
    *,
    report_url: str | None = None,
    config: dict[str, Any] | None = None,
    force: bool = False,
) -> NotifyResult:
    cfg = _merge_env(config or load_notifications())
    if not force and not should_notify(plans, cfg):
        result = NotifyResult(sent=[], skipped="silent_default")
        _log_notify(plans, result, report_url=report_url)
        return result
    message = build_summary(plans, report_url)
    result = NotifyResult(sent=dispatch_message(message, cfg, report_url=report_url))
    _log_notify(plans, result, report_url=report_url)
    return result


def _log_notify(
    plans: list[RepoPlan], result: NotifyResult, *, report_url: str | None
) -> None:
    urls = control_plane_urls()
    append_notification_log(
        {
            "human_count": sum(len(p.human_fixes) for p in plans),
            "channels": result.sent,
            "run_url": urls.get("run_url"),
            "inbox_url": urls.get("inbox_url"),
            "skipped": result.skipped,
            "status_url": report_url or urls.get("status_url"),
        }
    )
