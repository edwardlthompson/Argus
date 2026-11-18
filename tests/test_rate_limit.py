from __future__ import annotations

import time

from argus.rate_limit import CoreQuota, RateLimiter, SecondaryRateLimit


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


def test_core_quota_observe_and_budget():
    q = CoreQuota(reserve=100, calls_per_repo_estimate=50, max_wait_seconds=0.05)
    q.observe_headers(
        {"X-RateLimit-Limit": "5000", "X-RateLimit-Remaining": "50", "X-RateLimit-Reset": str(int(time.time()) + 1)}
    )
    assert q.limit == 5000
    assert q.remaining == 50
    assert q.needs_wait_for(200) is True
    assert q.adaptive_interval() >= q.min_interval
    q.ensure_budget(200)
    assert q.waits


def test_core_quota_no_wait_when_plenty():
    q = CoreQuota(reserve=100)
    q.observe_headers(
        {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4000",
            "X-RateLimit-Reset": str(int(time.time()) + 3600),
        }
    )
    assert q.needs_wait_for(300) is False
    assert q.adaptive_interval() <= q.max_interval
