"""Contract hash + RELEASE_TOKEN presence signals."""

from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.models import RepoRecord
from argus.paths import CONFIG_DIR, PROJECT_ROOT


def _hash_file(path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _controller_repo_names() -> frozenset[str]:
    """Names that may carry controller-only signals (RULES-STALE, release token)."""
    names = {"argus", "argus-runner"}
    try:
        from argus.config_loader import load_yaml

        data = load_yaml(CONFIG_DIR / "parent.yaml")
        for n in data.get("controller_repo_names") or []:
            if isinstance(n, str) and n.strip():
                names.add(n.strip().lower())
    except Exception:  # noqa: BLE001
        pass
    return frozenset(names)


def is_controller_repo(repo: RepoRecord) -> bool:
    return repo.name.lower() in _controller_repo_names()


def collect(client: GitHubClient, repo: RepoRecord) -> dict[str, Any]:
    """Local expected contract hash vs remote .argus/contract.json when present."""
    local = PROJECT_ROOT / "config" / "contract.sha256"
    expected = None
    if local.is_file():
        for line in local.read_text(encoding="utf-8").splitlines():
            bit = line.strip().split()[0] if line.strip() and not line.strip().startswith("#") else ""
            if len(bit) == 64:
                expected = bit.lower()
                break
    remote_hash = None
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/.argus/contract.json")
        if isinstance(data, dict) and data.get("sha"):
            # Git blob sha is not content sha256; use size+sha as stale proxy when expected set
            remote_hash = str(data.get("sha"))
    except GitHubError:
        remote_hash = None

    stale = bool(expected and remote_hash and expected != remote_hash)
    # Also compare content hash when we can decode
    content_hash = None
    try:
        data = client.get(f"/repos/{repo.owner}/{repo.name}/contents/.argus/contract.json")
        if isinstance(data, dict) and data.get("content"):
            import base64

            blob = base64.b64decode(data["content"])
            content_hash = hashlib.sha256(blob).hexdigest()
            if expected and content_hash != expected:
                stale = True
            elif expected and content_hash == expected:
                stale = False
    except (GitHubError, TypeError, ValueError):
        pass

    controller = is_controller_repo(repo)
    # Free-tier default: do not fan out process RELEASE_TOKEN to every portfolio repo.
    # Opt in with ARGUS_REQUIRE_RELEASE_TOKEN=1 (controller / runner only).
    require_token = os.environ.get("ARGUS_REQUIRE_RELEASE_TOKEN", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    token_set = bool(os.environ.get("RELEASE_TOKEN") or os.environ.get("ARGUS_RELEASE_TOKEN"))
    has_release_workflow = False
    if controller and require_token:
        try:
            workflows = client.get(f"/repos/{repo.owner}/{repo.name}/contents/.github/workflows")
            if isinstance(workflows, list):
                for item in workflows:
                    name = str(item.get("name") or "").lower()
                    if "release" in name:
                        has_release_workflow = True
                        break
        except GitHubError:
            pass
    else:
        # Not scoring SEC-RELEASE-TOKEN-MISSING on portfolio / free-tier.
        token_set = True
        has_release_workflow = False

    rules_stale = False
    if controller:
        try:
            from argus.rules_sync import rules_stale as _rules_stale

            rules_stale = _rules_stale()
        except Exception:  # noqa: BLE001
            rules_stale = False
    return {
        "contract_expected": expected,
        "contract_remote_sha": remote_hash,
        "contract_content_sha256": content_hash,
        "contract_stale": stale,
        "release_token_set": token_set,
        "has_release_workflow": has_release_workflow,
        "rules_stale": rules_stale,
        "CONTRACT-BEHIND": bool(stale),
        "RULES-STALE": rules_stale,
        "is_controller": controller,
    }


def local_contract_stale(expected_path=None, actual_path=None) -> bool:
    exp = _hash_file(expected_path or (PROJECT_ROOT / "config" / "contract.example.json"))
    act = _hash_file(actual_path or (PROJECT_ROOT / ".argus" / "contract.json"))
    if not exp or not act:
        return False
    return exp != act
