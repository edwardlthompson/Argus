"""Allowlist org / collaborator modes."""

from argus.discover import _allowed


def test_org_mode_filters_owner() -> None:
    allow = {"mode": "org", "orgs": ["Acme"], "allow": [], "deny": []}
    assert _allowed("Acme/app", "Acme", "me", allow)
    assert not _allowed("Other/app", "Other", "me", allow)


def test_collaborator_mode_allows() -> None:
    allow = {"mode": "collaborator", "allow": [], "deny": ["bad/x"]}
    assert _allowed("them/lib", "them", "me", allow)
    assert not _allowed("bad/x", "bad", "me", allow)


def test_owner_only() -> None:
    allow = {"mode": "owner_only", "allow": [], "deny": []}
    assert _allowed("me/a", "me", "me", allow)
    assert not _allowed("them/a", "them", "me", allow)
