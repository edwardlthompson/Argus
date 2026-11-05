# BUILD_PLAN — Argus

Status legend: 🔲 todo · ✅ done · ❌ blocked

## Product (do not drift)

<!-- product-brief-sync -->
Argus is a controller repository for multi-repo hygiene, scoring, safe auto-apply, gated agentic execution, and grandma-simple notifications. MIT. Python 3.11+. Portfolio doctor for the operator’s GitHub collection (including Argus itself). See `AGENT.md`.
<!-- /product-brief-sync -->

## Sequential

| Status | Venue | Task |
|--------|-------|------|
| ✅ | `[AGENT][LOCAL]` — scope: skeleton | Sprint 0: package, CLI stub, config loader, docs, MIT, CI |
| ✅ | `[AGENT][LOCAL]` — scope: discovery | Sprint 1: discovery, status.yaml, resolution cache, allow-list |
| ✅ | `[AGENT][LOCAL]` — scope: scoring | Sprint 2: signals, rubric, score, confidence |
| ✅ | `[AGENT][LOCAL]` — scope: compose | Sprint 3: fixes.yaml loader, compose rules, templates |
| ✅ | `[AGENT][LOCAL]` — scope: apply | Sprint 4: apply.py dry-run + PR preference |
| ✅ | `[AGENT][LOCAL]` — scope: notify | Sprint 5: notify + grandma HTML |
| ✅ | `[AGENT][LOCAL]` — scope: agents | Sprint 6: agent_dispatch + circuit breaker |
| ✅ | `[AGENT][LOCAL]` — scope: multiuser | Sprint 7: profiles, report-only, FORKING/THIRD_PARTY docs |
| ✅ | `[AGENT][LOCAL]` — scope: harden | Sprint 8: fixtures, rate limits, doctor harden, Pages publish |
| ✅ | `[AGENT][LOCAL]` — scope: parent-child | Align as child of agent-project-bootstrap; close `docs/PARENT_GAP_LIST.md` |
| ✅ | `[AGENT][LOCAL]` — scope: archived-filter | Exclude archived from default discover; `--include-archived` |
| ✅ | `[AGENT][LOCAL]` — scope: expanded-signals | Signals: PRs, issues, security alerts, Dependabot, CodeQL, releases, lineage |
| ✅ | `[AGENT][LOCAL]` — scope: expanded-fixes | Expand fixes catalogue (`config/fixes/*.yaml`) + gates |
| ✅ | `[AGENT][LOCAL]` — scope: lineage | `parent.yaml` + lineage signal + version/gap fixes |
| ✅ | `[AGENT][LOCAL]` — scope: real-apply | Real `auto_safe` handlers (topics, description, file/content PRs) |
| ✅ | `[AGENT][LOCAL]` — scope: fix-cli | `argus fix [--apply] [--agent]` batch + worktree dispatch |
| ✅ | `[AGENT][LOCAL]` — scope: notify-wire | Weekly notify path; `.env.example` + START_HERE notifications |
| ✅ | `[AGENT][LOCAL]` — scope: publish | Publish `edwardlthompson/Argus`; enable Actions/Pages — see `docs/PUBLISH.md` |
| ✅ | `[AGENT][LOCAL]` — scope: self-scan | Discovery/allowlist includes controller; no skip-self; PUBLISH.md |
| ✅ | `[AGENT][LOCAL]` — scope: doctor-tests | Fixtures, apply mocks, docs, CHANGELOG, snapshots, verify |

## Parallel (after Sequential)

None — sequential board complete.
