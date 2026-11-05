from __future__ import annotations

import time

from argus.rate_limit import RateLimiter, SecondaryRateLimit


def test_rate_limiter_paces():
    limiter = RateLimiter(min_interval=0.05)
    t0 = time.monotonic()
    limiter.wait()
    limiter.wait()
    assert time.monotonic() - t0 >= 0.04


def test_secondary_backoff_resets():
    sb = SecondaryRateLimit(base_seconds=0.01, max_seconds=0.05)
    sb.on_failure()
    assert sb.failures == 1
    sb.on_success()
    assert sb.failures == 0
