from __future__ import annotations

from argus.models import RepoStatus
from argus.state import StateStore


def test_new_and_removed_detection(tmp_path):
    store = StateStore(tmp_path / "t.sqlite")
    store.upsert_repo("a/one", RepoStatus.ACTIVE)
    store.upsert_repo("a/two", RepoStatus.ACTIVE)
    known = set(store.known_repos())
    current = {"a/one", "a/three"}
    new = sorted(current - known)
    removed = sorted(known - current)
    assert new == ["a/three"]
    assert removed == ["a/two"]
    store.mark_inactive("a/two")
    assert store.known_repos()["a/two"]["active"] is False
    store.close()


def test_resolution_ttl(tmp_path):
    store = StateStore(tmp_path / "r.sqlite")
    store.record_resolution("a/one", "FIX", ttl_days=30)
    assert store.is_resolved("a/one", "FIX")
    store.close()
