# Architecture

Argus is a **controller repository**. It never permanently lives inside product repos. Privileged and agentic work originates here; targets receive reviewed Pull Requests.

```
discover → signals → score → match fixes → compose → auto-apply → agent dispatch → notify
                ↑                         ↓
              state ←────────────── resolution cache
```

## Packages

| Module | Role |
|--------|------|
| `discover.py` | List repos, detect new/removed, honour allow-list |
| `signals/` | Pure collectors per category |
| `score.py` | Deterministic attention score from `rubric.yaml` |
| `match.py` + `expr.py` | Safe `applies_when` evaluation |
| `compose.py` | Runbook + HTML (nine composition rules) |
| `apply.py` | `auto_safe` only; prefers PRs; dry-run |
| `board_classify.py` / `board_normalize.py` | APB BUILD_PLAN marker-lane append + divergent restructure |
| `dependabot_policy.py` | Mode-aware bump levels (patch/minor vs all) |
| `agent_dispatch.py` | Gated prompts + circuit breaker |
| `notify.py` | Silent unless human/critical work |
| `state.py` | SQLite status, resolutions, history |

## Config is behaviour

Weights, fixes, notifications, safety limits, and profiles live under `config/`. Forks adapt by editing YAML, not Python.

## Modes

- **run** — full portfolio path
- **report** — forced read-only (`GitHubClient.report_only=True`); no writes
- **doctor** — validate token + config

`signals/board.py` classifies `BUILD_PLAN.md` (root, else `docs/BUILD_PLAN.md`) as canonical / partial / divergent / missing. Partial boards get `BOARD-MARKERS`; divergent boards get `BOARD-RESTRUCTURE`.

## Gates

Every `agent` and `auto_safe` fix must declare an executable `gate`. Composition always ends each agent phase with `GATE: …`. A phase without a gate is a build failure (loader + tests enforce this).
