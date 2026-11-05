# Changelog

## [Unreleased]

### Added

- Portfolio icon standard (`config/profile_icons.yaml`, `docs/PROFILE_ICONS.md`) + hygiene `BRAND-ICON-MISSING` for missing/stub marks.
- Featured showcase stats under each app name (stars · watches · forks); `max_featured_repos: 0` shows all eligible projects.

### Changed

- Profile Overview portfolio polish: live languages + FOSS devicons, auto skill cards (`profile_skills.yaml`), centered HTML hero/banner, featured icon grid (no traffic/pins/topics dump).
- Profile redesign pass: banner-carried identity (no H1/tagline dupe), skip throwaway bios, wide OG featured cards + captions, richer banner, empty YAML roles → live auto cards.
- Profile gap close: curated `featured_repos` + icon tree scan/`icon_overrides`, grouped stack (`profile_stack.yaml`), richer self-hosted banner + drop-in docs, GitHub contact badge, `current_focus` / `open_to_cards`, featured star captions.

## [0.3.0] — 2026-11-05

### Added

- Dual-plane docs + `bootstrap-argus-runner.*`; doctor public-controller guard; profile Overview compose/PR (`PROF-README`).
- Projects v2 inbox sync; `repository_dispatch` scan; profile packs; org/collaborator discover; hygiene signals (SPDX, CODEOWNERS, stale branches).
- `argus explain` / `inbox` / `status --safe` / `report --open`; notify quiet hours + digest coalesce; auto-safe CODEOWNERS/gitignore/CodeQL + Dependabot/secret-scan API; dry-run `would_prs`.
- CodeQL, gitleaks, SBOM workflows; pinned CI Action SHAs; `update-deps` / `gc-worktrees` / encoding gates.

## [0.2.0] — 2026-11-05

### Added

- Cursor FOSS parity: `.cursor/commands/` (45), hooks, curated skills/subagents, `argus-foss` plugin, thin `scripts/agent-run.py` shim (G13 closed).
- Private control plane: status-only public Pages; GitHub Issues inbox (`argus-inbox`); full report as Actions artifacts (30d); safe chat digests with Issue/Actions deep links; `scan.yml` workflow_dispatch.
- Initial Argus controller: discovery, signals, scoring, fix catalogue, composition, dry-run auto-apply, notifications, agent dispatch, report-only mode, CLI, docs, and fixture snapshot tests (Sprints 0–7).
- Sprint 8 hardening: archived/experimental fixtures, depends_on + gate tests, API rate limiter, doctor safety checks, GitHub Pages workflow for `report.html`.
- Declared product-child lineage to `edwardlthompson/agent-project-bootstrap@1.12.0`; closed `docs/PARENT_GAP_LIST.md` (G01–G11, G13; G12/G14/G15 wont).
- Portfolio doctor: skip archived by default; lineage/PR/CI/security signals; real `auto_safe` apply; `argus fix [--apply] [--agent]`; notify env secrets + weekly wire; publish docs for self-scan.

### Changed

- Public Pages no longer publish `report.html` / runbook / inbox detail (attacker checklist risk).
- `scripts/verify.*` invoke ruff via `python -m ruff` for PATH-safe Windows runs.
