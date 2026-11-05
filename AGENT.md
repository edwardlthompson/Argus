# Argus — product brief (do not drift)

**Product:** Argus  
**Purpose:** Controller repository for autonomous multi-repo hygiene, scoring, safe auto-apply, gated agentic execution, grandma-simple notifications, and a public skills portfolio Overview generated from live repo evidence.  
**License:** MIT  
**Stack:** Python 3.11+  
**Parent:** [edwardlthompson/agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap) (product child — see `docs/PARENT_GAP_LIST.md`)  

## Non-negotiables

1. Every agent-executed phase ends with an explicit executable GATE.
2. Human instructions are grandma-simple (prefer GitHub UI).
3. Prefer PRs over direct commits to targets.
4. Never destroy data (no hard deletes, no history rewrite).
5. Deterministic scoring/composition — no LLMs on that path.
6. Behaviour in YAML/JSON config, not hard-coded Python.
7. Graceful degradation on token/rate/permission failures.

## Primary outputs

`dist/runbook.md`, `dist/report.html`, notifications, optional PRs into target repos.
