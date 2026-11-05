"""Thin GitHub REST client with graceful degradation."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from argus.rate_limit import RateLimiter, SecondaryRateLimit


class GitHubError(RuntimeError):
    """GitHub API failure."""


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = "https://api.github.com",
        timeout: float = 30.0,
        report_only: bool = False,
        min_interval: float = 0.05,
    ) -> None:
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
        self.base_url = base_url.rstrip("/")
        self.report_only = report_only
        self.write_attempts = 0
        self._limiter = RateLimiter(min_interval=min_interval)
        self._secondary = SecondaryRateLimit()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "argus-controller",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self._client = httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, *, allow_write: bool = False, **kwargs: Any) -> Any:
        mutating = method.upper() not in {"GET", "HEAD"}
        if mutating:
            self.write_attempts += 1
            if self.report_only or not allow_write:
                raise GitHubError(
                    f"Write blocked (report_only={self.report_only}, allow_write={allow_write}): "
                    f"{method} {path}"
                )

        retries = 3
        for _attempt in range(retries):
            self._limiter.wait()
            resp = self._client.request(method, path, **kwargs)
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                self._secondary.on_failure()
                reset = resp.headers.get("X-RateLimit-Reset")
                if reset and reset.isdigit():
                    sleep_for = max(0, int(reset) - int(time.time()))
                    time.sleep(min(sleep_for, 60))
                continue
            if resp.status_code >= 400:
                raise GitHubError(f"{method} {path} -> {resp.status_code}: {resp.text[:200]}")
            self._secondary.on_success()
            if resp.status_code == 204:
                return None
            return resp.json()
        raise GitHubError(f"Rate limited after retries: {method} {path}")

    def get(self, path: str, **kwargs: Any) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, *, allow_write: bool = False, **kwargs: Any) -> Any:
        return self._request("POST", path, allow_write=allow_write, **kwargs)

    def patch(self, path: str, *, allow_write: bool = False, **kwargs: Any) -> Any:
        return self._request("PATCH", path, allow_write=allow_write, **kwargs)

    def put(self, path: str, *, allow_write: bool = False, **kwargs: Any) -> Any:
        return self._request("PUT", path, allow_write=allow_write, **kwargs)

    def whoami(self) -> dict[str, Any]:
        return self.get("/user")

    def list_viewer_repos(
        self, *, affiliation: str = "owner,collaborator,organization_member"
    ) -> list[dict[str, Any]]:
        return self._paginate(
            "/user/repos",
            {"affiliation": affiliation, "sort": "updated"},
        )

    def list_user_repos(self, username: str, *, public_only: bool = False) -> list[dict[str, Any]]:
        type_param = "public" if public_only else "owner"
        return self._paginate(f"/users/{username}/repos", {"type": type_param, "sort": "updated"})

    def list_org_repos(self, org: str, *, public_only: bool = False) -> list[dict[str, Any]]:
        type_param = "public" if public_only else "all"
        return self._paginate(f"/orgs/{org}/repos", {"type": type_param, "sort": "updated"})

    def get_repo(self, owner: str, name: str) -> dict[str, Any]:
        return self.get(f"/repos/{owner}/{name}")

    def _paginate(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        repos: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self.get(path, params={**params, "per_page": 100, "page": page})
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return repos
