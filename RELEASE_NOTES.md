# Release notes — Argus 0.5.0

## Highlights

- **Dual-plane YOLO** — Public product ships `apply_mode: normal` (safe to share). Private runner bootstrap arms `yolo.on` + hands-off micromanage. Kill switches: delete `yolo.on`, `YOLO-OFF.md`, `argus off`.
- **Signals (S9)** — Brand icon states (`owned`/`inherited`/`missing`/`placeholder`) with brief-only PRs (no PNG generation); orphans probe; UX rule loader; `CONTRACT-STALE` / `SEC-RELEASE-TOKEN-MISSING`; Grok budget + circuit breaker (`config/grok_bots.yaml`).
- **Staging + triage (S10)** — UX rollout observe→soft→enforce; `argus triage` / `--fleet`; YOLO consumes agent-class deterministic handlers only.
- **Rules → fleet → remote (S11–S15)** — `argus.upstream.json` + `argus rules sync|diff|bump`; `RULES-STALE` blocks YOLO; fleet plan/execute/drift/revert/halt + action ledger; `argus.remote.json` readonly by default; CLI `digest` / `focus` / `cost` / `fleet` / `rules` / `off`.

## Upgrade notes

- Re-bootstrap or manually add `yolo.on` on the **private runner** only. Do not arm YOLO on the public product template.
- After pulling rule/config changes: `argus rules sync` so `RULES-STALE` clears.
- Grok digests honor daily caps in `config/grok_bots.yaml`; clear `GROK-OFF.md` only after reviewing breaker trips.
- Prefer `python scripts/agent-run.py verify` before merge.

See `CHANGELOG.md` for the full list.
