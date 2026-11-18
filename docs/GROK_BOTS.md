# Grok Bots (draft / digest layer)

Optional [Grok Bots](https://docs.x.ai/grok-bot/skills-routines-and-automations) sit **beside** Argus. They cut **attention** load (notice + draft). Argus + Dependabot own **mechanical** fixes. Grok **never** merges, force-pushes, or edits Settings/secrets.

Policy ADR: [`docs/adr/0001-grok-bots-draft-digest-and-yolo.md`](adr/0001-grok-bots-draft-digest-and-yolo.md). YOLO (auto-merge gated PRs): [`docs/YOLO.md`](YOLO.md).

## Budget (enforced)

Single source of truth: [`config/grok_bots.yaml`](../config/grok_bots.yaml). Counters live in `dist/grok-budget.json`. Circuit breaker writes sticky `GROK-OFF.md`.

| Control | Default |
|---------|---------|
| Allowlist max repos | 3 |
| `max_runs_per_bot_per_day` | 2 (1 scheduled + 1 on-demand) |
| `max_total_bot_runs_per_day` | 8 |
| `max_output_lines` / PRs / issues | ≤40 / ≤30 / ≤15 |
| `max_estimated_tokens_per_day` | 50000 |
| `cooldown_hours` | 20 |
| Circuit breaker | 3 empty/error digests → `GROK-OFF.md` |

`argus doctor` reports budget file + breaker state. Identity stays comment-only PAT; **never** merge; separate from `ARGUS_GITHUB_TOKEN`.

## Shared foundation

| Piece | Rule |
|-------|------|
| Identity | Dedicated GitHub machine user or fine-grained PAT: read contents/actions/issues/PRs/metadata; write **issue comments** only. No admin, no merge. |
| Plugin | Grok GitHub plugin (separate from `ARGUS_GITHUB_TOKEN` on the private runner). |
| Allowlist | Start with `YOU/Argus` + at most two product apps. Expand only after a quiet week. |
| Output | ≤40 lines markdown. Prefer links over pasted blobs. |
| Caps | See `config/grok_bots.yaml` (≤40 lines; ≤30 PRs; ≤15 issues). |
| Test | Three supervised Test runs before enabling each routine. |

**Shared skill preamble** (paste into every skill — numbers must match `config/grok_bots.yaml`):

```text
Repos allowlist only. Never merge, never push to default branch, never change Settings/secrets.
If data missing: say so; do not invent. Prefer links over pasted blobs.
Hard caps (config/grok_bots.yaml): max_runs_per_bot_per_day=2; max_total_bot_runs_per_day=8;
max_output_lines=40; max_prs_per_run=30; max_issues_per_run=15; max_estimated_tokens_per_day=50000;
cooldown_hours=20. Stop if GROK-OFF.md exists.
Draft / digest / handoff only. Argus applies gated fixes; you do not.
```

Copy-paste skill bodies: [`docs/grok-bots/`](grok-bots/).

## Workload split

| Layer | Job | Auto-apply? |
|-------|-----|-------------|
| Dependabot / `update-deps` | Patch/minor bumps | PR; YOLO may auto-merge **patch** |
| Argus `auto_safe` | Mechanical hygiene + gate | PR; YOLO may auto-merge when CI green |
| Argus gated agent | Scoped riskier fixes + gate | PR; YOLO optional after gate+CI |
| Grok Bot | Notice, draft, inbox handoff | **Never** merge or silent push |

Prefer growing Argus matchers/`auto_safe` over giving Grok write power.

## Bots (8)

### High sense (Wave A)

| Bot | Trigger | Writes | YOLO |
|-----|---------|--------|------|
| **CI Watchdog** | Daily schedule (prefer) or allowlisted `workflow_run` failure | One digest (chat or private Issue `ci-digest YYYY-MM-DD`) | May file `argus-inbox` handoff brief; **no** Grok PR |
| **Release Notes** | On-demand or tag/release | Draft release body / CHANGELOG in chat | Draft only — human publishes |
| **Triage / Repro** | Issue labeled `needs-repro` only | One Issue comment (repro pack) | Optional Argus agent handoff from brief; no Grok push |

### Worth considering (Wave B)

| Bot | Trigger | Writes | YOLO |
|-----|---------|--------|------|
| **Tuesday Steward** | Tuesday schedule (after Monday Dependabot + Argus weekly) | One `steward-digest YYYY-MM-DD`; optional single `argus-inbox` handoff | Digest only — Argus YOLO already fixed/merged what policy allows |
| **Stale PR Nudge** | Weekly | One Slack/chat table (metadata only) | Argus may close abandoned *bot* PRs per policy; human PRs stay listed |
| **Security / Dependabot digest** | Weekly | Grandma checklist (titles + severity + URL, cap 15) | Argus auto-merges Dependabot after CI green (vanilla patch+minor; YOLO all levels); Grok does not bump |
| **Argus Inbox Translator** | Weekly or on-demand | ≤15 checklist lines from private `argus-inbox` | Less needed if Argus already applying; still useful for human leftovers |
| **Incident postmortem stub** | `@mention` only | Timeline draft | Never auto |
| **Docs / CHANGELOG helper** | `@mention` or after Release Notes | Keep-a-Changelog draft | Same Bot as Release Notes (second skill); draft only |

Skill body: [`docs/grok-bots/09-tuesday-steward.md`](grok-bots/09-tuesday-steward.md).

## Handoff format (CI / repro → Argus)

When YOLO or apply mode should pick up work, Grok opens/updates a **private** runner Issue with label `argus-inbox` (and optional `grok-handoff`):

```markdown
## Argus handoff
- repo: OWNER/NAME
- kind: ci-failure | needs-repro
- url: <Actions run or Issue>
- summary: ≤3 bullets
- suggested_fix_class: <optional id from config/fixes*.yaml>
- do_not: invent patches; Argus owns apply
```

## Explicit non-goals

- Grok auto-bumping dependencies
- Per-failure CI LLM fix storms
- Portfolio-wide “watch everything” listeners
- Replacing Argus `auto_safe` or local Cursor `/fix` gates
- Two competing autofixers (Grok must not open code PRs)

## Operator setup checklist

1. Create Bot GitHub user / PAT (comment-only).
2. Connect Grok GitHub plugin; paste allowlist into each skill.
3. Enable Wave A skills from `docs/grok-bots/` (3 Test runs each).
4. Add Wave B after a quiet week.
5. Keep Dependabot + `argus fix` / runner `apply` for mutators.
6. Optional later: [`docs/YOLO.md`](YOLO.md) for auto-merge.

### Automate Tuesday Steward pack

xAI has **no create-Bot API**. Argus packs a one-paste bootstrap:

```bash
argus grok pack tuesday-steward --allowlist YOU/Argus
# → dist/grok-bots/tuesday-steward-bootstrap.md
```

Paste that file into a new Grok Bot chat (creates skill + Tuesday routine). After Argus weekly runs, open Actions artifact `health-infographic.html` / `health-hotspots.json` for before→after problem hotspots. Optional: set runner secrets `GROK_STEWARD_WEBHOOK_URL` + `GROK_STEWARD_WEBHOOK_KEY` so `argus-weekly` pings the Steward routine.
