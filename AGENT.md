# Argus — product brief (do not drift)

**Product:** Argus  
**Purpose:** The enforcer. Multi-repo hygiene controller that reads parent rules, reports, gates, and — when armed on a **private runner** — fixes, merges, fans out, and answers cards. It never invents rules. Public product stays safe to share; private runner micromanages the operator’s portfolio so they can stay creative.  
**License:** MIT  
**Stack:** Python 3.11+  
**Parent:** [edwardlthompson/agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap) (product child — see `docs/PARENT_GAP_LIST.md`)  

## Dual plane (do not drift)

| Plane | YOLO |
|-------|------|
| Public product / template (`Argus`) | **Off** — `apply_mode: normal`, no `yolo.on` |
| Private runner (`YOU/argus-runner`) | **On** — bootstrap drops `yolo.on` + yolo defaults; hands-off micromanage |

Don’t bother the creator: one log line per run; leftovers → private `yolo-digest`; no per-finding spam. Kill switches: delete `yolo.on`, `YOLO-OFF.md`, `GROK-OFF.md`, `argus off`.

## Non-negotiables

1. Every agent-executed phase ends with an explicit executable GATE.
2. Human instructions are grandma-simple (prefer GitHub UI).
3. Prefer PRs over direct commits to targets.
4. Never destroy data (no hard deletes, no history rewrite).
5. Deterministic scoring/composition — no LLMs on that path.
6. Behaviour in YAML/JSON config, not hard-coded Python.
7. Graceful degradation on token/rate/permission failures.
8. Never invent rules — sync/enforce from parent; Argus applies.

## Primary outputs

`dist/runbook.md`, `dist/report.html`, notifications, optional PRs into target repos; private `argus-history/` audit ledger.

## Profile Overview (operators)

Public `YOU/YOU` skills portfolio README from live GitHub evidence. Start from `config/profile_readme.yaml.example`, then follow [`docs/PROFILE_OVERVIEW.md`](docs/PROFILE_OVERVIEW.md). Behaviour stays in YAML (`profile_readme`, `profile_skills`, `profile_stack`, `profile_icons`). YOLO skips Overview mutations by default (`skip_profile`).
