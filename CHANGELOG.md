# Changelog

## [Unreleased]

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
