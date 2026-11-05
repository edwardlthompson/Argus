"""GitHub API pacing: primary core quota + secondary back-off."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Sleeps when called faster than `min_interval` seconds between ticks."""

    min_interval: float = 0.05
    _last: float = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        gap = self.min_interval - (now - self._last)
        if gap > 0:
            time.sleep(gap)
        self._last = time.monotonic()

    def set_interval(self, seconds: float) -> None:
        self.min_interval = max(0.0, seconds)


@dataclass
class SecondaryRateLimit:
    """Exponential back-off after secondary rate-limit signals."""

    base_seconds: float = 1.0
    max_seconds: float = 60.0
    failures: int = 0

    def on_success(self) -> None:
        self.failures = 0

    def on_failure(self) -> float:
        self.failures += 1
        delay = min(self.max_seconds, self.base_seconds * (2 ** (self.failures - 1)))
        time.sleep(delay)
        return delay


@dataclass
class CoreQuota:
    """Track REST core quota from X-RateLimit-* headers (authenticated default 5000/hr)."""

    limit: int = 5000
    remaining: int | None = None
    reset_at: float = 0.0
    reserve: int = 200
    min_interval: float = 0.05
    max_interval: float = 2.0
    calls_per_repo_estimate: int = 50
    max_wait_seconds: float = 3700.0
    request_count: int = 0
    waits: list[str] = field(default_factory=list)

    def observe_headers(self, headers: dict[str, str] | object) -> None:
        get = headers.get if hasattr(headers, "get") else lambda _k, _d=None: None
        lim = get("X-RateLimit-Limit") or get("x-ratelimit-limit")
        rem = get("X-RateLimit-Remaining") or get("x-ratelimit-remaining")
        reset = get("X-RateLimit-Reset") or get("x-ratelimit-reset")
        if lim is not None and str(lim).isdigit():
            self.limit = int(lim)
        if rem is not None and str(rem).isdigit():
            self.remaining = int(rem)
        if reset is not None and str(reset).isdigit():
            self.reset_at = float(reset)
        self.request_count += 1

    def seconds_until_reset(self, *, now: float | None = None) -> float:
        now = time.time() if now is None else now
        if self.reset_at <= 0:
            return 0.0
        return max(0.0, self.reset_at - now)

    def adaptive_interval(self) -> float:
        """Pace harder when remaining budget is tight vs time to reset."""
        if self.remaining is None:
            return self.min_interval
        secs = self.seconds_until_reset()
        if secs <= 0 or self.remaining <= 0:
            return self.max_interval
        # leave reserve; spread usable calls over remaining window
        usable = max(1, self.remaining - self.reserve)
        paced = secs / usable
        return min(self.max_interval, max(self.min_interval, paced))

    def needs_wait_for(self, needed: int) -> bool:
        if self.remaining is None:
            return False
        return self.remaining < max(needed, self.reserve)

    def wait_until_reset(self, *, reason: str = "core_quota") -> float:
        delay = min(self.max_wait_seconds, self.seconds_until_reset() + 1.0)
        if delay <= 0:
            delay = min(60.0, self.max_wait_seconds)
        self.waits.append(f"{reason}:{int(delay)}s")
        time.sleep(delay)
        return delay

    def ensure_budget(self, needed: int) -> None:
        """Block until remaining can cover `needed` calls (+ reserve policy)."""
        if not self.needs_wait_for(needed):
            return
        self.wait_until_reset(reason=f"need_{needed}")

    def snapshot(self) -> dict[str, object]:
        return {
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_at": self.reset_at,
            "seconds_until_reset": round(self.seconds_until_reset(), 1),
            "reserve": self.reserve,
            "request_count": self.request_count,
            "calls_per_repo_estimate": self.calls_per_repo_estimate,
            "waits": list(self.waits),
        }
