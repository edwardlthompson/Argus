"""Thin GitHub REST client with graceful degradation."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from argus.rate_limit import CoreQuota, RateLimiter, SecondaryRateLimit


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
        quota: CoreQuota | None = None,
    ) -> None:
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
        self.base_url = base_url.rstrip("/")
        self.report_only = report_only
        self.write_attempts = 0
        self.quota = quota or CoreQuota(min_interval=min_interval)
        self._limiter = RateLimiter(min_interval=self.quota.min_interval)
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

    def refresh_rate_limit(self) -> dict[str, Any]:
        """GET /rate_limit (does not consume core quota). Updates self.quota."""
        last_exc: Exception | None = None
        for attempt in range(6):
            self._limiter.wait()
            try:
                resp = self._client.request("GET", "/rate_limit")
            except (
                httpx.RemoteProtocolError,
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.ConnectTimeout,
            ) as exc:
                last_exc = exc
                time.sleep(min(2 ** attempt, 20))
                continue
            if resp.status_code >= 400:
                raise GitHubError(f"GET /rate_limit -> {resp.status_code}: {resp.text[:200]}")
            data = resp.json()
            core = (data.get("resources") or {}).get("core") or data.get("rate") or {}
            if "limit" in core:
                self.quota.limit = int(core["limit"])
            if "remaining" in core:
                self.quota.remaining = int(core["remaining"])
            if "reset" in core:
                self.quota.reset_at = float(core["reset"])
            return data if isinstance(data, dict) else {}
        raise GitHubError(f"GET /rate_limit transport: {last_exc}")

    def ensure_budget(self, needed: int) -> None:
        """Refresh quota if unknown/low, then wait until `needed` calls fit."""
        if self.quota.remaining is None or self.quota.needs_wait_for(needed):
            try:
                self.refresh_rate_limit()
            except GitHubError:
                pass
        self.quota.ensure_budget(needed)
        # After a wait, refresh so remaining is accurate.
        if self.quota.remaining is not None and self.quota.remaining < needed:
            try:
                self.refresh_rate_limit()
            except GitHubError:
                pass

    def _request(
        self, method: str, path: str, *, allow_write: bool = False, read_post: bool = False, **kwargs: Any
    ) -> Any:
        mutating = method.upper() not in {"GET", "HEAD"} and not read_post
        if mutating:
            self.write_attempts += 1
            if self.report_only or not allow_write:
                raise GitHubError(
                    f"Write blocked (report_only={self.report_only}, allow_write={allow_write}): "
                    f"{method} {path}"
                )
        for attempt in range(6):
            self._limiter.set_interval(self.quota.adaptive_interval())
            self._limiter.wait()
            if self.quota.remaining is not None and self.quota.remaining <= 0:
                self.quota.wait_until_reset(reason="remaining_zero")
                try:
                    self.refresh_rate_limit()
                except GitHubError:
                    pass
            try:
                resp = self._client.request(method, path, **kwargs)
            except (
                httpx.RemoteProtocolError,
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.ConnectTimeout,
            ) as exc:
                self._secondary.on_failure()
                time.sleep(min(2 ** attempt, 20))
                if attempt >= 5:
                    raise GitHubError(f"{method} {path} transport: {exc}") from exc
                continue
            self.quota.observe_headers(resp.headers)
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                self._secondary.on_failure()
                reset = resp.headers.get("X-RateLimit-Reset")
                if reset and reset.isdigit():
                    self.quota.reset_at = float(reset)
                    self.quota.remaining = 0
                self.quota.wait_until_reset(reason=f"http_403_attempt_{attempt}")
                try:
                    self.refresh_rate_limit()
                except GitHubError:
                    pass
                continue
            if resp.status_code == 429:
                self._secondary.on_failure()
                retry_after = resp.headers.get("Retry-After")
                if retry_after and str(retry_after).isdigit():
                    time.sleep(min(int(retry_after), int(self.quota.max_wait_seconds)))
                else:
                    self.quota.wait_until_reset(reason=f"http_429_attempt_{attempt}")
                continue
            if resp.status_code >= 400:
                raise GitHubError(f"{method} {path} -> {resp.status_code}: {resp.text[:200]}")
            self._secondary.on_success()
            return None if resp.status_code == 204 else resp.json()
        raise GitHubError(f"Rate limited after retries: {method} {path}")

    def get(self, path: str, **kwargs: Any) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, *, allow_write: bool = False, **kwargs: Any) -> Any:
        return self._request("POST", path, allow_write=allow_write, **kwargs)

    def patch(self, path: str, *, allow_write: bool = False, **kwargs: Any) -> Any:
        return self._request("PATCH", path, allow_write=allow_write, **kwargs)

    def put(self, path: str, *, allow_write: bool = False, **kwargs: Any) -> Any:
        return self._request("PUT", path, allow_write=allow_write, **kwargs)

    def delete(self, path: str, *, allow_write: bool = False, **kwargs: Any) -> Any:
        return self._request("DELETE", path, allow_write=allow_write, **kwargs)

    def whoami(self) -> dict[str, Any]:
        return self.get("/user")

    def list_viewer_repos(
        self, *, affiliation: str = "owner,collaborator,organization_member"
    ) -> list[dict[str, Any]]:
        return self._paginate("/user/repos", {"affiliation": affiliation, "sort": "updated"})

    def list_user_repos(self, username: str, *, public_only: bool = False) -> list[dict[str, Any]]:
        kind = "public" if public_only else "owner"
        return self._paginate(f"/users/{username}/repos", {"type": kind, "sort": "updated"})

    def list_org_repos(self, org: str, *, public_only: bool = False) -> list[dict[str, Any]]:
        kind = "public" if public_only else "all"
        return self._paginate(f"/orgs/{org}/repos", {"type": kind, "sort": "updated"})

    def get_repo(self, owner: str, name: str) -> dict[str, Any]:
        return self.get(f"/repos/{owner}/{name}")

    def graphql(
        self, query: str, variables: dict[str, Any] | None = None, *, allow_write: bool = False
    ) -> dict[str, Any]:
        is_mut = allow_write or query.lstrip().lower().startswith("mutation")
        data = self._request(
            "POST", "/graphql", allow_write=is_mut, read_post=not is_mut,
            json={"query": query, "variables": variables or {}},
        )
        if not isinstance(data, dict):
            raise GitHubError("GraphQL returned non-object")
        if data.get("errors"):
            raise GitHubError(f"GraphQL errors: {data['errors']!r}"[:200])
        result = data.get("data")
        if not isinstance(result, dict):
            raise GitHubError("GraphQL missing data")
        return result

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
