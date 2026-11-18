# Plan — Argus

## Milestone 0 (done)

Skeleton → discovery → scoring → composition → auto-apply → notify → agent dispatch → multi-user report → hardening (BUILD_PLAN Sprints 0–8).

## Milestone 1 (next)

- First real `argus run --dry-run` against the operator portfolio; triage human tasks
- Enable GitHub Pages for status-only `status.html` (`pages` workflow); full report via Actions artifacts + Issues inbox
- Optional: adopt parent `check-template-updates` script on `/upgrade`

## Risks

| Risk | Mitigation |
|------|------------|
| Over-automation | Only `auto_safe`; circuit breaker on agent gates |
| Blast radius | Allow-list `owner_only`; max PRs/run |
| Parent drift | `.template-version` + `docs/PARENT_GAP_LIST.md` |
