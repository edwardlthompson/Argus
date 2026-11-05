"""Projects v2 inbox sync (mocked GraphQL)."""

from __future__ import annotations

from typing import Any

from argus.inbox_project import sync_inbox_project


class FakeClient:
    def __init__(self) -> None:
        self.writes: list[tuple[str, dict[str, Any]]] = []

    def graphql(
        self, query: str, variables: dict[str, Any] | None = None, *, allow_write: bool = False
    ) -> dict[str, Any]:
        variables = variables or {}
        if "projectV2(number" in query.replace(" ", ""):
            return {"user": {"projectV2": {"id": "PROJ"}}, "organization": {"projectV2": None}}
        if "items(first" in query.replace(" ", "") or "items(first:100" in query:
            return {
                "node": {
                    "items": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [{"id": "item1", "content": {"id": "ISSUE_EXISTING", "number": 1}}],
                    }
                }
            }
        if allow_write:
            self.writes.append((query, variables))
            return {"addProjectV2ItemById": {"item": {"id": "new"}}}
        return {}

    def get(self, path: str, **kwargs: Any) -> Any:
        return []


def test_skip_when_no_project_number() -> None:
    r = sync_inbox_project(FakeClient(), dry_run=True, config={"controller_repo": "a/b"})  # type: ignore[arg-type]
    assert r.added == [] and r.dry_run_would_add == []


def test_dry_run_lists_new_issues() -> None:
    cfg = {"controller_repo": "me/runner", "project_number": 3, "label_inbox": "argus-inbox"}
    nodes = [
        {"id": "ISSUE_EXISTING", "number": 1},
        {"id": "ISSUE_NEW", "number": 2},
    ]
    r = sync_inbox_project(FakeClient(), dry_run=True, config=cfg, issue_nodes=nodes)  # type: ignore[arg-type]
    assert r.skipped == ["#1"]
    assert r.dry_run_would_add == ["#2"]


def test_apply_adds_missing() -> None:
    client = FakeClient()
    cfg = {"controller_repo": "me/runner", "project_number": 3}
    nodes = [{"id": "ISSUE_NEW", "number": 9}]
    r = sync_inbox_project(client, dry_run=False, config=cfg, issue_nodes=nodes)  # type: ignore[arg-type]
    assert r.added == ["#9"]
    assert client.writes
