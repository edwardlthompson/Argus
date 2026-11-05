# Decision log

## 2026-11-05 — Ship v0.3.0 (Sequential A–L)

- **Decision:** Release dual-plane + profile Overview + operator/auto_safe expansion as **0.3.0** (not 0.2.x) after empty-board cleanup.
- **Deps:** `update-deps` scoped to pyproject direct deps; pip-audit on those requirements only (ignore global site-packages noise).
- **Gates:** verify + smoke-sprint green (64 tests); template Release Please / full pre-release-gate remain N/A (G12/G14).

## 2026-11-05 — Public product + private runner + profile Overview

- **Decision:** Keep Argus **public** for MIT sharing. Run auto-scan / auto-fix / Issues on a **private** `argus-runner`. Do not make the product agent-only; Actions is the cron brain.
- **Profile:** Maintain public `USERNAME/USERNAME` Overview README via PR from live API + YAML voice (no LLM on compose path). BryantuAi-like IA; text-first; pins remain human UI.
- **Safety:** `security_issues: true` only on private controller; doctor warns if public + security Issues.

## 2026-11-04 — Parent/child lineage

- **Decision:** Treat Argus as a product child of `edwardlthompson/agent-project-bootstrap` v1.12.0, not a nested StarRupture app and not a full template fork.
- **Closed:** G01–G11, G13 (Cursor FOSS pack). **Wont:** G12/G14/G15 (full lifecycle, modules/examples, optional CodeQL later as board J1).
