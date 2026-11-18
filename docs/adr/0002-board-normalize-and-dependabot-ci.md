# ADR 0002 — BUILD_PLAN APB hygiene; Dependabot CI-green auto-merge

- **Status:** Accepted
- **Date:** 2026-11-14
- **Deciders:** Argus maintainers

## Context

Edward’s portfolio boards diverge from agent-project-bootstrap `BUILD_PLAN_TEMPLATE.md` (missing marker lanes, or custom formats). A News Bot appends P1/P2 rows into `local-agent-lane` or a `## News inbox (synced)` section. Argus’s board listed “filing portfolio findings as BUILD_PLAN chores” as a non-goal — format hygiene is different.

Dependabot squash-merge (`merge_dependabot_patch_prs`) skipped `evaluate_pre_merge`, treated `*_patch` keys as patch+minor, and YOLO could merge without CI. Vanilla `--apply` did not auto-merge Dependabot. `skip_ci_when_actions_unavailable` must not bypass CI for dependency bumps.

## Decision

1. **`BOARD-MARKERS`** (`auto_safe`): locate root `BUILD_PLAN.md` else `docs/BUILD_PLAN.md`; append missing APB markers; fold News inbox into `local-agent-lane` (AGENT) or Waiting on a person (HUMAN); gate = markers present.
2. **`BOARD-RESTRUCTURE`** (`agent` + YOLO mechanical handler): rebuild divergent boards to APB shape; preserve every open task and completed history (pointer to `COMPLETED_TASKS.md` OK); write root `BUILD_PLAN.md` when the board lived in `docs/`. Never invent work. PR on `chore/argus-*`.
3. **Dependabot:** YOLO auto-merges all bump levels including major; vanilla `--apply` auto-merges patch+minor. Both require `evaluate_pre_merge` with actually-green CI. Empty/never-started checks stay open. `skip_ci_when_actions_unavailable` does not apply.
4. Config keys: `normal.merge_dependabot` + `dependabot_auto_merge_levels`; `yolo.auto_merge_dependabot` + `dependabot_auto_merge_levels`. `*_patch` names remain aliases.

## Alternatives considered

| Alternative | Why not |
|-------------|---------|
| File findings as BUILD_PLAN chores | Violates continuous-zero non-goal; this work is format only |
| Invent CI patches so Dependabot can merge when Actions is down | Forbidden; leave the PR open |
| Soft-allowlist Dependabot like upgrade noise | Dependency bumps are not template hygiene |

## Consequences

- Catalogue: `config/fixes/portfolio.yaml`. Policy: `argus/dependabot_policy.py`, `config/safety.yaml`.
- Private `argus-runner` should pick up new `safety.yaml` keys (defaults cover old `*_patch` aliases).
- Docs: `docs/SAFETY.md`, `docs/YOLO.md`, `docs/RUNNER.md`.

### Critique

| Issue | Resolution |
|-------|------------|
| Partial vs divergent mis-classifies Argus table board | Venue tags `[LOCAL]`/`[CLOUD]` count as APB-ish → marker append only |
| YOLO majors too aggressive | Operator sets `dependabot_auto_merge_levels`; CI green still required |
| News inbox lost if lanes missing | Append stubs first, then fold |
