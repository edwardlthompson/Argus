"""Quiet hours helper."""

from argus.notify import _in_quiet_hours


def test_quiet_disabled():
    assert not _in_quiet_hours({"quiet_hours": {"enabled": False}})


def test_quiet_window_wraps():
    # Cannot assert current hour; just ensure no crash for wrap window.
    _in_quiet_hours(
        {"quiet_hours": {"enabled": True, "timezone": "UTC", "start_hour": 22, "end_hour": 8}}
    )
