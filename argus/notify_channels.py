"""Channel dispatch for Argus notifications."""

from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from typing import Any
from urllib import request


def post_json(url: str, payload: dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with request.urlopen(req, timeout=20) as resp:  # noqa: S310 — operator-configured URL
        resp.read()


def send_email(cfg: dict[str, Any], body: str) -> None:
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


def dispatch_message(
    message: str, cfg: dict[str, Any], *, report_url: str | None = None
) -> list[str]:
    sent: list[str] = []
    discord = cfg.get("discord") or {}
    if discord.get("enabled") and discord.get("webhook_url"):
        post_json(discord["webhook_url"], {"content": message})
        sent.append("discord")
    telegram = cfg.get("telegram") or {}
    if telegram.get("enabled") and telegram.get("bot_token") and telegram.get("chat_id"):
        url = f"https://api.telegram.org/bot{telegram['bot_token']}/sendMessage"
        post_json(url, {"chat_id": telegram["chat_id"], "text": message})
        sent.append("telegram")
    webhook = cfg.get("webhook") or {}
    if webhook.get("enabled") and webhook.get("url"):
        post_json(webhook["url"], {"text": message, "report_url": report_url})
        sent.append("webhook")
    email = cfg.get("email") or {}
    if email.get("enabled"):
        send_email(email, message)
        sent.append("email")
    return sent
