# Completed tasks

Archived BUILD_PLAN rows (newest first).

## Overview sync + Fleet report (2026-11-12)

- ✅ `[AGENT][LOCAL]` — scope: `sync_profile,profile_enrich,weekly.yml` | Weekly Overview refresh (stars/forks/views/icons/membership)
- ✅ `[AGENT][LOCAL]` — scope: `report_view,templates` | Single Fleet table + attention bar; Assessment last; Issues then PRs sort
- ✅ `[AGENT][LOCAL]` — scope: reports | Split Issues from open PRs (no false-positive Issues)

## Continuous zero + Issue triage (2026-11-12)

- ✅ `[AGENT][LOCAL]` — scope: `config/safety.yaml,config_loader` | **CZ1** continuous-zero safety flags
- ✅ `[AGENT][LOCAL]` — scope: `argus/signals/contract.py` | **CZ2** RULES-STALE / RELEASE_TOKEN fan-out fix
- ✅ `[AGENT][LOCAL]` — scope: `argus/yolo.py,pipeline.py` | **CZ3** handlers + pipeline loop
- ✅ `[AGENT][LOCAL]` — scope: `config/fixes/` | **CZ4** CodeQL/lineage/Dependabot/catalogue
- ✅ `[AGENT][LOCAL]` — scope: docs | **CZ5** YOLO/SAFETY continuous-zero docs
- ✅ `[AGENT][LOCAL]` — scope: `report_view,yolo_issues` | Priority by GH Issues; ISSUE-PATTERNED-AUTO triage

## Free-tier Actions-out (no payment) (2026-11-11)

- ✅ `[AGENT][LOCAL]` — scope: free-tier-actions | **F1** — `skip_ci_when_actions_unavailable` + doctor probe + `local-weekly` / `--actions-unavailable`; cleared ExpeditionGauge#36, JanusBoot#13, point-and-shoot#42 without paid CI. Paying for Actions is never required.

## argus-weekly repair W1–W6 + S1–S2 (2026-11-11)

- ✅ `[HUMAN][PC]` — scope: Actions secrets | **W1 Token** — Verified `ARGUS_GITHUB_TOKEN` on **`edwardlthompson/argus-runner`** (updated 2026-11-11). Local `argus doctor` / whoami OK with portfolio PAT. End-to-end weekly still blocked by W5 (jobs never start).
- ✅ `[HUMAN][PC]` — scope: workflow | **W2 Re-run** — Actions weekly blocked by billing; substituted with `argus merge-upgrades --allow-unarmed` + `local-weekly` (merged hover-icons#37, noclip-auto#17 via billing soft-ok).
- ✅ `[HUMAN][PC]` — scope: runner | **W3 Where it runs** — Confirmed: public Argus `weekly.yml` dispatch-only; runner Tuesday `0 14 * * 2` cron + Steward webhook body.
- ✅ `[AGENT][LOCAL]` — scope: PRs | **W4 Dependabot** — Merged Actions bumps (#1,#2,#3,#4) + setup-python@v7 locally (closes #7 intent); **hold** pytest/pytest-cov majors (#6,#9).
- ✅ `[AGENT][LOCAL]` — scope: actions-fallback | **W6 Actions-out fallback** — `argus local-weekly` + `scripts/local-weekly.ps1|.sh`; `yolo.merge_when_actions_billing` merges upgrades when every failed check is billing-only.
- ✅ `[AGENT][LOCAL]` — scope: yolo | **S1 Trivy wave** — npm/Guava fixers applied; re-merge via W6 or after W5 CI green.
- ✅ `[AGENT][LOCAL]` — scope: noclip-auto#17 | **S2 noclip** — Merged via W6 billing soft-ok (11/11 failed checks were spending-limit annotations).

## Parent v1.13.0 child upgrades U1–U7 (2026-11-11)

- ✅ `[AGENT][LOCAL]` — scope: `scripts/,BUILD_PLAN.md,dist/` | **U1 Tooling** — `scripts/child-upgrade-1.13.py` canon pack + inventory
- ✅ `[AGENT][LOCAL]` — scope: fleet | **U2 Canary** — `edwardlthompson/lineage-lens` full upgrade PR
- ✅ `[AGENT][LOCAL]` — scope: fleet | **U3 Batch** — AstroAlarm, HermesLauncher, SyncMark
- ✅ `[AGENT][LOCAL]` — scope: fleet | **U4 Batch** — chromaflow, OBDForge, JanusBoot, continuum-calendar, QuickMediaIngest
- ✅ `[AGENT][LOCAL]` — scope: fleet | **U5 Batch** — selfchronicle, ExpeditionGauge, takein-sms, hover-icons, 3d-game-optimizer
- ✅ `[AGENT][LOCAL]` — scope: fleet | **U6 Batch** — vault-organizer, noclip-auto, trendalgo-bot, MultiAppShare-, DevPulse
- ✅ `[AGENT][LOCAL]` — scope: fleet | **U7 Batch** — OpenShouter, point-and-shoot, QRaft, screen-wakelock-detector, starrupture-city-planner, aetherfeed, bl4-forge, Argus (product-safe pack)

## Signals → fleet → YOLO → remote S9–S15 (2026-11-09)

- ✅ `[AGENT][LOCAL]` — scope: `argus/,config/,docs/,scripts/,tests/` | **S9 Signals** — brand states, orphans, UX baseline, contract/token, grok budget, dual-plane YOLO defaults
- ✅ `[AGENT][LOCAL]` — scope: `argus/,config/,state/` | **S10 Staging + triage** — ux_rollout observe→soft→enforce; `argus triage` / `--fleet`
- ✅ `[AGENT][LOCAL]` — scope: `argus/,config/` | **S11 Rule sync** — `argus.upstream.json`, cache, RULES-STALE, lock/diff/bump
- ✅ `[AGENT][LOCAL]` — scope: `argus/,config/,docs/` | **S12 Fleet + audit/undo** — plan/execute/drift/revert/halt + action ledger
- ✅ `[AGENT][LOCAL]` — scope: `argus/,docs/,scripts/` | **S13 YOLO arming (runner)** — `yolo.on`, six checks, undo ladder, hands-off digest
- ✅ `[AGENT][LOCAL]` — scope: `argus/,config/` | **S14 Remote readonly→arm** — remote.json, cards, quiet_hours, `argus off`
- ✅ `[AGENT][LOCAL]` — scope: `argus/cli.py,docs/` | **S15 Command surface** — digest/focus/fleet/rules/cost verbs

## Dual-plane + profile + Sequential A–L (2026-11-05)

- ✅ `[AUTO][LOCAL]` — scope: dual-plane-runner | **A1.** Private `edwardlthompson/argus-runner` created; secret set; inbox pointed; scan dry-run queued — `scripts/bootstrap-argus-runner.*`
- ✅ `[AGENT][LOCAL]` — scope: dual-plane-docs | **A2.** Rewrite FORKING/START_HERE/PUBLISH/SAFETY — public source, private runner, no findings on public Argus
- ✅ `[AGENT][LOCAL]` — scope: inbox-defaults | **A3.** `inbox.yaml` example → `YOUR_LOGIN/argus-runner`; `security_issues: false` default; docs when true (private only)
- ✅ `[AGENT][LOCAL]` — scope: doctor-public-guard | **A4.** Doctor warns if apply / security Issues against a public controller
- ✅ `[AGENT][LOCAL]` — scope: memory-adr-dual | **A5.** Refresh AGENT_MEMORY + DECISION_LOG (public product, private runner, profile Overview)
- ✅ `[AGENT][LOCAL]` — scope: runner-workflows-docs | **B1.** Document weekly/scan `apply` + token scopes on private runner
- ✅ `[AGENT][LOCAL]` — scope: weekly-apply-runbook | **B2.** First weekly `--apply` operator runbook (dry-run then apply)
- ✅ `[AGENT][LOCAL]` — scope: threat-model | **B3.** Threat model — runner PAT blast radius; public vs private surfaces
- ✅ `[AGENT][LOCAL]` — scope: human-backlog | **B4.** HUMAN_BACKLOG.md for Settings tasks
- ✅ `[AGENT][LOCAL]` — scope: first-30-days | **B5.** FIRST_30_DAYS for Argus operators (dual-plane)
- ✅ `[AGENT][LOCAL]` — scope: profile-config-template | **C1.** `config/profile_readme.yaml` + `templates/profile_readme.md.j2` (BryantuAi IA; a11y; text-first)
- ✅ `[AGENT][LOCAL]` — scope: profile-compose | **C2.** Compose README from user API + portfolio languages/topics/top repos + YAML voice
- ✅ `[AGENT][LOCAL]` — scope: profile-apply | **C3.** `PROF-README` + `sync_profile_readme` PR to public `USER/USER` (create if missing); marker; tests
- ✅ `[AGENT][LOCAL]` — scope: profile-docs | **C4.** START_HERE/FORKING — Overview updates via PR; suggested pins = human
- ✅ `[AGENT][LOCAL]` — scope: notify-artifact-link | **D1.** Artifact deep-link in notify (private runner run URL)
- ✅ `[AGENT][LOCAL]` — scope: chat-scan-dispatch | **D2.** Discord/Telegram → `repository_dispatch` on private runner
- ✅ `[AGENT][LOCAL]` — scope: project-board-sync | **D3.** GitHub Project sync for `argus-inbox`
- ✅ `[AGENT][LOCAL]` — scope: status-badge | **D4.** Status badge SVG (counts only)
- ✅ `[AGENT][LOCAL]` — scope: notify-log-status | **D5.** Notification log on status page (safe fields)
- ✅ `[AGENT][LOCAL]` — scope: org-discover | **E1.** Org-scoped discover mode
- ✅ `[AGENT][LOCAL]` — scope: collaborator-filter | **E2.** Team/collaborator repo filter
- ✅ `[AGENT][LOCAL]` — scope: stale-branch-signal | **E3.** Stale-branch signal
- ✅ `[AGENT][LOCAL]` — scope: license-signal | **E4.** License SPDX signal
- ✅ `[AGENT][LOCAL]` — scope: branch-protection-signal | **E5.** CODEOWNERS / branch-protection signal
- ✅ `[AGENT][LOCAL]` — scope: actions-cost-signal | **E6.** Actions billing / minutes heuristic
- ✅ `[AGENT][LOCAL]` — scope: explain-score | **E7.** `argus explain REPO` attention-score dump
- ✅ `[AGENT][LOCAL]` — scope: profile-packs | **E8.** Profile packs (library / game / android / docs)
- ✅ `[AGENT][LOCAL]` — scope: auto-safe-templates | **F1.** More `auto_safe` file templates (SECURITY/CONTRIBUTING/CODEOWNERS)
- ✅ `[AGENT][LOCAL]` — scope: dependabot-api | **F2.** Dependabot enable via API when permitted
- ✅ `[AGENT][LOCAL]` — scope: secret-scan-api | **F3.** Secret-scanning / push-protection API toggle
- ✅ `[AGENT][LOCAL]` — scope: codeql-pr-pack | **F4.** CodeQL workflow PR pack for targets
- ✅ `[AGENT][LOCAL]` — scope: gitignore-autosafe | **F5.** `.gitignore` hygiene `auto_safe`
- ✅ `[AGENT][LOCAL]` — scope: topic-taxonomy | **F6.** Topic taxonomy config
- ✅ `[AGENT][LOCAL]` — scope: dry-run-preview-json | **F7.** Dry-run “would PR” preview JSON
- ✅ `[AGENT][LOCAL]` — scope: blast-radius-caps | **F8.** Max-blast-radius per-owner caps in safety.yaml
- ✅ `[AGENT][LOCAL]` — scope: worktree-cleanup | **G1.** Worktree cleanup after agent batch (real `gc-worktrees`)
- ✅ `[AGENT][LOCAL]` — scope: gate-fail-issue | **G2.** Gate failure → Issue on controller (private runner)
- ✅ `[AGENT][LOCAL]` — scope: prompt-budget | **G3.** Prompt size budget report
- ✅ `[AGENT][LOCAL]` — scope: circuit-status | **G4.** Circuit-breaker on status page
- ✅ `[AGENT][LOCAL]` — scope: email-doctor | **H1.** Email path smoke test in doctor
- ✅ `[AGENT][LOCAL]` — scope: quiet-hours | **H2.** Quiet hours / timezone for notifies
- ✅ `[AGENT][LOCAL]` — scope: digest-coalesce | **H3.** Digest coalescing (daily max)
- ✅ `[AGENT][LOCAL]` — scope: doctor-channels | **H4.** Per-channel enable in `argus doctor`
- ✅ `[AGENT][LOCAL]` — scope: inbox-cli | **I1.** `argus inbox` list/sync dry-run
- ✅ `[AGENT][LOCAL]` — scope: status-cli | **I2.** `argus status` safe counts
- ✅ `[AGENT][LOCAL]` — scope: report-open | **I3.** `argus report --open` local HTML
- ✅ `[AGENT][LOCAL]` — scope: windows-path-docs | **I4.** Windows PATH install docs
- ✅ `[AGENT][LOCAL]` — scope: shell-completion | **I5.** Click shell completion
- ✅ `[AGENT][LOCAL]` — scope: codeql-self | **J1.** CodeQL workflow for public Argus (G15)
- ✅ `[AGENT][LOCAL]` — scope: pip-audit-verify | **J2.** pip-audit in verify/CI
- ✅ `[AGENT][LOCAL]` — scope: gitleaks-ci | **J3.** Gitleaks / secret scan in CI
- ✅ `[AGENT][LOCAL]` — scope: pin-actions | **J4.** Pinned Actions SHAs
- ✅ `[AGENT][LOCAL]` — scope: sbom-release | **J5.** SBOM on release
- ✅ `[AGENT][LOCAL]` — scope: upgrade-dry-run | **K1.** `/upgrade` dry-run against parent 1.12+
- ✅ `[AGENT][LOCAL]` — scope: update-deps-shim | **K2.** Real `update-deps` shim (pip outdated + patch apply)
- ✅ `[AGENT][LOCAL]` — scope: encoding-verify | **K3.** `check-file-encoding` in verify
- ✅ `[AGENT][LOCAL]` — scope: destructive-ops-rule | **K4.** Thin `destructive-ops.mdc` honesty labels
- ✅ `[AGENT][LOCAL]` — scope: pack-plugin | **K5.** Pack script for `argus-foss` plugin
- ✅ `[AGENT][LOCAL]` — scope: offline-fixtures | **L1.** Demo fixture portfolio offline
- ✅ `[AGENT][LOCAL]` — scope: third-party-pages | **L2.** Public report-only Pages for third-party (counts only)
- ✅ `[AGENT][LOCAL]` — scope: shareable-runbook | **L3.** Signed shareable runbook export
- ✅ `[AGENT][LOCAL]` — scope: github-app-guide | **L4.** Read-only GitHub App install guide
- ✅ `[AGENT][LOCAL]` — scope: cf-access-dashboard | **L5.** Cloudflare Access gated dashboard (Phase 2)
- ✅ `[AGENT][LOCAL]` — scope: oauth-mini-inbox | **L6.** OAuth mini-app inbox (Phase 2)

## Argus board archive — Sprints 0–8 + portfolio doctor + control plane + Cursor FOSS (2026-11-05)

- ✅ `[AGENT][LOCAL]` — scope: skeleton | Sprint 0: package, CLI stub, config loader, docs, MIT, CI
- ✅ `[AGENT][LOCAL]` — scope: discovery | Sprint 1: discovery, status.yaml, resolution cache, allow-list
- ✅ `[AGENT][LOCAL]` — scope: scoring | Sprint 2: signals, rubric, score, confidence
- ✅ `[AGENT][LOCAL]` — scope: compose | Sprint 3: fixes.yaml loader, compose rules, templates
- ✅ `[AGENT][LOCAL]` — scope: apply | Sprint 4: apply.py dry-run + PR preference
- ✅ `[AGENT][LOCAL]` — scope: notify | Sprint 5: notify + grandma HTML
- ✅ `[AGENT][LOCAL]` — scope: agents | Sprint 6: agent_dispatch + circuit breaker
- ✅ `[AGENT][LOCAL]` — scope: multiuser | Sprint 7: profiles, report-only, FORKING/THIRD_PARTY docs
- ✅ `[AGENT][LOCAL]` — scope: harden | Sprint 8: fixtures, rate limits, doctor harden, Pages publish
- ✅ `[AGENT][LOCAL]` — scope: parent-child | Align as child of agent-project-bootstrap; close `docs/PARENT_GAP_LIST.md`
- ✅ `[AGENT][LOCAL]` — scope: archived-filter | Exclude archived from default discover; `--include-archived`
- ✅ `[AGENT][LOCAL]` — scope: expanded-signals | Signals: PRs, issues, security alerts, Dependabot, CodeQL, releases, lineage
- ✅ `[AGENT][LOCAL]` — scope: expanded-fixes | Expand fixes catalogue (`config/fixes/*.yaml`) + gates
- ✅ `[AGENT][LOCAL]` — scope: lineage | `parent.yaml` + lineage signal + version/gap fixes
- ✅ `[AGENT][LOCAL]` — scope: real-apply | Real `auto_safe` handlers (topics, description, file/content PRs)
- ✅ `[AGENT][LOCAL]` — scope: fix-cli | `argus fix [--apply] [--agent]` batch + worktree dispatch
- ✅ `[AGENT][LOCAL]` — scope: notify-wire | Weekly notify path; `.env.example` + START_HERE notifications
- ✅ `[AGENT][LOCAL]` — scope: publish | Publish `edwardlthompson/Argus`; enable Actions/Pages — see `docs/PUBLISH.md`
- ✅ `[AGENT][LOCAL]` — scope: self-scan | Discovery/allowlist includes controller; no skip-self; PUBLISH.md
- ✅ `[AGENT][LOCAL]` — scope: doctor-tests | Fixtures, apply mocks, docs, CHANGELOG, snapshots, verify
- ✅ `[AGENT][LOCAL]` — scope: private-control-plane | Status-only Pages; Issues inbox; private artifacts; safe notify; scan.yml
- ✅ `[AGENT][LOCAL]` — scope: cursor-foss | Slash commands, hooks, curated skills/agents, argus-foss plugin, agent-run shim
