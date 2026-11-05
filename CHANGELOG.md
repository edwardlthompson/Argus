# Changelog

## [Unreleased]

### Added

- Initial Argus controller: discovery, signals, scoring, fix catalogue, composition, dry-run auto-apply, notifications, agent dispatch, report-only mode, CLI, docs, and fixture snapshot tests (Sprints 0–7).
- Sprint 8 hardening: archived/experimental fixtures, depends_on + gate tests, API rate limiter, doctor safety checks, GitHub Pages workflow for `report.html`.
- Declared product-child lineage to `edwardlthompson/agent-project-bootstrap@1.12.0`; closed `docs/PARENT_GAP_LIST.md` (G01–G11; G12–G15 wont).
- Portfolio doctor: skip archived by default; lineage/PR/CI/security signals; real `auto_safe` apply; `argus fix [--apply] [--agent]`; notify env secrets + weekly wire; publish docs for self-scan.
