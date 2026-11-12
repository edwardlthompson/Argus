"""Unit: free-tier Actions outage detection + merge-when-unavailable defaults."""

from __future__ import annotations

import os

from argus.actions_billing import (
    BILLING_MARKERS,
    actions_unavailable,
    is_billing_text,
    reset_actions_unavailable_cache,
    summarize_billing,
)


def test_billing_markers_cover_spending_limit():
    msg = (
        "The job was not started because recent account payments have failed "
        "or your spending limit needs to be increased. Please check the "
        "'Billing & plans' section in your settings"
    )
    assert is_billing_text(msg)
    assert any(m in msg.lower() for m in BILLING_MARKERS)
    assert not is_billing_text("Trivy found CRITICAL vulnerability in npm")
    assert not is_billing_text("")


def test_summarize_billing():
    assert summarize_billing({"billing": False}) == ""
    assert "actions_billing" in summarize_billing(
        {"billing": True, "failed": ["Security Scan", "Trivy FS Scan"]}
    )


def test_merge_when_actions_billing_default():
    from argus.config_loader import load_safety

    yolo = load_safety().get("yolo") or {}
    assert yolo.get("merge_when_actions_billing") is True
    assert yolo.get("skip_ci_when_actions_unavailable") is True


def test_actions_unavailable_env_override(monkeypatch):
    reset_actions_unavailable_cache()
    monkeypatch.setenv("ARGUS_ACTIONS_UNAVAILABLE", "1")

    class _NoClient:
        pass

    assert actions_unavailable(_NoClient(), safety={}) is True  # type: ignore[arg-type]
    reset_actions_unavailable_cache()
    monkeypatch.setenv("ARGUS_ACTIONS_UNAVAILABLE", "0")
    assert actions_unavailable(_NoClient(), safety={}) is False  # type: ignore[arg-type]
    reset_actions_unavailable_cache()
    monkeypatch.delenv("ARGUS_ACTIONS_UNAVAILABLE", raising=False)
    assert "ARGUS_ACTIONS_UNAVAILABLE" not in os.environ
