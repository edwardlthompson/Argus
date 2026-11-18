from __future__ import annotations

from argus.inbox_guard import check_public_controller_risks


def test_placeholder_ok_when_security_off():
    assert check_public_controller_risks(
        None, config={"controller_repo": "YOUR_LOGIN/argus-runner", "security_issues": False}
    ) == []


def test_placeholder_bad_when_security_on():
    probs = check_public_controller_risks(
        None, config={"controller_repo": "YOUR_LOGIN/argus-runner", "security_issues": True}
    )
    assert probs


class _FakeClient:
    def __init__(self, private: bool) -> None:
        self.private = private

    def get(self, path: str, **kwargs):  # noqa: ANN003
        return {"private": self.private, "full_name": "acme/argus-runner"}


def test_public_controller_with_security_flagged():
    probs = check_public_controller_risks(
        _FakeClient(False),  # type: ignore[arg-type]
        config={"controller_repo": "acme/argus-runner", "security_issues": True},
    )
    assert any("PUBLIC" in p for p in probs)


def test_private_controller_ok():
    assert (
        check_public_controller_risks(
            _FakeClient(True),  # type: ignore[arg-type]
            config={"controller_repo": "acme/argus-runner", "security_issues": True},
        )
        == []
    )
