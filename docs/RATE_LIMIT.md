# GitHub API rate limits (Argus)

## Exact quotas (authenticated token)

From `GET https://api.github.com/rate_limit` (this call **does not** consume core quota):

| Resource | Limit | Notes |
|----------|-------|--------|
| **REST `core`** | **5000 / hour** | Every `GET/POST/PATCH/PUT` to `api.github.com` except GraphQL |
| GraphQL | 5000 **points** / hour | Argus barely uses this today |
| Search | 30 / minute | Not used by portfolio scan |
| Unauthenticated | 60 / hour | Never run Argus without `GITHUB_TOKEN` |

Fine-grained PATs and classic PATs both get **5000 core/hour** for normal user tokens. GitHub Apps can differ by installation.

Live check:

```bash
argus doctor
# or:
curl -sH "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
```

## Why the cleanup burned the hour

Signal collection is ~**45–60 REST calls per repo** (hygiene file probes, CI, deps, traffic, …).  
31 repos × ~50 ≈ **1,500+** calls per full scan. Two apply passes + retries easily exceed **5000**.

Old client only waited ≤60s × 3 on `403 rate limit`, then raised — while reset was still many minutes away.

## How Argus batches now

Configured in [`config/safety.yaml`](../config/safety.yaml) → `github_api`:

| Key | Default | Role |
|-----|---------|------|
| `core_limit_hint` | 5000 | Documented ceiling (live headers win) |
| `reserve` | 250 | Never spend the last N calls |
| `calls_per_repo_estimate` | 50 | Budget math per repo |
| `max_repos_per_batch` | 6 | Scan N repos, re-check budget, continue |
| `min_interval_ms` / `max_interval_ms` | 80 / 2000 | Adaptive pacing from remaining ÷ time-to-reset |
| `max_wait_seconds` | 3700 | Cap for wait-until-reset sleeps |

Behavior:

1. Before each repo **batch**, ensure `remaining ≥ batch×estimate + reserve` (refresh `/rate_limit`, **wait until reset** if short).
2. Every response updates quota from `X-RateLimit-*` headers; interval lengthens when budget is tight.
3. On `403 rate limit` / `429`, **sleep until reset** (not a 60s give-up), then continue.
4. Apply caps `max_auto_prs_per_run` further by remaining budget (~8 calls/PR).

Rough safe throughput: with reserve 250, ~**4750** usable calls/hour ≈ **~95 repos/hour** at 50 calls/repo, or **~1–2 full 31-repo scans/hour** if you also apply. Prefer **one scan + one apply**, then wait for reset before another full pass.

## Apply history (private runner)

Every fix/run appends `dist/APPLY_HISTORY.md` + `dist/apply-history.jsonl`. On apply (not report-only), Argus also updates `argus-history/` on the **private** controller (`config/inbox.yaml` → `controller_repo`, e.g. `YOU/argus-runner`). Public product repos never get this write.

## Operator tips

- Run `argus doctor` before a big cleanup; if `remaining` &lt; `reserve`, wait.
- Prefer `--skip-profile` when not updating Overview (fewer calls).
- Do not chain dry-run → apply → dry-run → apply in the same hour without checking quota.
- Lower `max_repos_per_batch` / raise `reserve` on a shared PAT.
