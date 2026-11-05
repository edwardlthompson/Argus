# ADR 0001 — Grok Bots draft/digest; Argus owns auto-fix; optional YOLO

- **Status:** Accepted
- **Date:** 2026-11-05
- **Deciders:** Argus maintainers

## Context

Operators want less portfolio babysitting. Grok Bots can watch GitHub and draft text, but free-form LLM “auto-fix” fights Argus’s gate/PR model and often increases review load. Argus already has `auto_safe`, gated agents, Dependabot, dry-run vs apply, and safety caps.

## Decision

1. **Grok Bots** = notice, digest, draft, and optional `argus-inbox` handoff. No merge, no default-branch push, no Settings/secrets.
2. **Argus + Dependabot** = sole mutators for mechanical and gated fixes.
3. **Optional YOLO** (`apply_mode: yolo` in `config/safety.yaml`) = Argus apply + auto-merge of green gated/`auto_safe` (and Dependabot **patch**) PRs. Hard floors stay: never force-push, never delete repos, prefer PRs, allowlist, gates, circuit breaker.
4. Release notes, CHANGELOG, and incident stubs stay **draft-only** even under YOLO.
5. Prefer growing Argus `auto_safe` matchers over granting Grok write power.

## Alternatives considered

| Alternative | Why not |
|-------------|---------|
| Grok opens fix PRs | No gate contract; duplicate autofixer; token burn |
| No Grok at all | Leaves continuous CI/attention gaps Argus scan does not cover |
| YOLO = silent push to default branch | Violates prefer-PRs / safety invariants |

## Consequences

- Docs: `docs/GROK_BOTS.md`, `docs/YOLO.md`, skill templates under `docs/grok-bots/`.
- Config stub: `apply_mode` + `yolo` keys in `safety.yaml` (auto-merge wiring is operator GitHub rulesets / follow-on apply code).
- Operators graduate: normal → apply → yolo → kill switch.

### Critique

| Issue | Resolution |
|-------|------------|
| Two autofixers | Grok never merges; Argus sole applicator |
| YOLO includes product bugs | Unlabeled creative work excluded; `needs-repro` + gate only |
| Operator forgets YOLO | Document kill switch + grandma summary of merges |
| Stub without merge code | Config/docs first; merge via GitHub auto-merge until Argus implements post-check merge |
