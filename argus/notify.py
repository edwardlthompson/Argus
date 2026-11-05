"""Notifications: email, Discord, Telegram, generic webhook. Silent by default."""

from __future__ import annotations

import json
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any
from urllib import request

from argus.config_loader import load_notifications
from argus.models import RepoPlan


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
            alerts = 0
            # deps open alerts may appear via score notes only; category security is enough
            if alerts:
                return True
    return False


def build_summary(plans: list[RepoPlan], report_url: str | None = None) -> str:
    human = sum(len(p.human_fixes) for p in plans)
    if human == 0:
        return "Argus finished with no human tasks."
    noun = "task" if human == 1 else "tasks"
    link = f"\nReport: {report_url}" if report_url else ""
    return f"Argus needs you for {human} small {noun}.{link}"


def send_error_notification(message: str, *, report_url: str | None = None) -> NotifyResult:
    cfg = _merge_env(load_notifications())
    if not cfg.get("notify_on_run_error", True):
        return NotifyResult(sent=[], skipped="errors_disabled")
    text = f"Argus run failed: {message}"
    if report_url:
        text += f"\nReport: {report_url}"
    return _dispatch_message(text, cfg, report_url=report_url)


def send_notifications(
    plans: list[RepoPlan],
    *,
    report_url: str | None = None,
    config: dict[str, Any] | None = None,
    force: bool = False,
) -> NotifyResult:
    cfg = _merge_env(config or load_notifications())
    if not force and not should_notify(plans, cfg):
        return NotifyResult(sent=[], skipped="silent_default")

    message = build_summary(plans, report_url)
    return _dispatch_message(message, cfg, report_url=report_url)


def _dispatch_message(
    message: str, cfg: dict[str, Any], *, report_url: str | None = None
) -> NotifyResult:
    sent: list[str] = []

    discord = cfg.get("discord") or {}
    if discord.get("enabled") and discord.get("webhook_url"):
        _post_json(discord["webhook_url"], {"content": message})
        sent.append("discord")

    telegram = cfg.get("telegram") or {}
    if telegram.get("enabled") and telegram.get("bot_token") and telegram.get("chat_id"):
        url = f"https://api.telegram.org/bot{telegram['bot_token']}/sendMessage"
        _post_json(url, {"chat_id": telegram["chat_id"], "text": message})
        sent.append("telegram")

    webhook = cfg.get("webhook") or {}
    if webhook.get("enabled") and webhook.get("url"):
        _post_json(webhook["url"], {"text": message, "report_url": report_url})
        sent.append("webhook")

    email = cfg.get("email") or {}
    if email.get("enabled"):
        _send_email(email, message)
        sent.append("email")

    return NotifyResult(sent=sent)


def _post_json(url: str, payload: dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=20) as resp:  # noqa: S310 — operator-configured URL
        resp.read()


def _send_email(cfg: dict[str, Any], body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = cfg.get("subject", "Argus needs you")
    msg["From"] = cfg["from"]
    msg["To"] = cfg["to"]
    msg.set_content(body)
    host = cfg.get("smtp_host", "localhost")
    port = int(cfg.get("smtp_port", 587))
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        if cfg.get("use_tls", True):
            smtp.starttls()
        if cfg.get("username"):
            smtp.login(cfg["username"], cfg.get("password", ""))
        smtp.send_message(msg)
