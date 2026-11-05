"""Simple token-bucket style back-off helpers for GitHub API pacing."""

from __future__ import annotations

import time
from dataclasses import dataclass


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
