# Decision log

## 2026-11-12 — Ship v0.9.0 (Overview weekly sync + Fleet report)

- **Decision:** `sync_profile` refreshes Overview on every apply / Tuesday / `local-weekly` (stats, icons, public↔private) while `skip_profile` only blocks auto_safe into `YOU/YOU`. Reports use one Fleet table (Issues → PRs, attention bar); Assessment at bottom.
- **Gates:** `update-deps` audit clean + `verify` (162 tests); template Release Please / full pre-release-gate N/A (G12).
- **Ops:** Keep runner `weekly.yml` on `--with-profile`; free-tier `local-weekly --apply` remains the cadence.

## 2026-11-12 — Ship v0.8.0 (continuous zero + patterned Issues)

- **Decision:** Continuous zero is product policy (`safety.normal` + `yolo`): auto rules sync, deterministic handlers on `--apply`, CI soft-resolve when Actions unavailable, second pass. Patterned Issue close (`argus-auto` / digests / bot bumps) only — never invent product patches. Report Priority sorted by GitHub Issues; omit green+zero.
- **Gates:** `update-deps` audit clean + `verify` (158 tests); template Release Please / full pre-release-gate N/A (G12).
- **Ops:** `/ship` amid low disk — ephemeral purge; free-tier `local-weekly --apply` remains the cadence.

## 2026-11-10 — Ship v0.6.0 (hands-off upgrade YOLO + Tuesday Steward)

- **Decision:** Soft-merge allowlisted template noise + mechanical upgrade fixers are **on** for scheduled YOLO; Tuesday weekly after Monday Dependabot; Grok Tuesday Steward is digest-only (pack bootstrap, no create API).
- **Gates:** `update-deps` (click 8.5.1) + `verify` (132 tests); template Release Please / full pre-release-gate N/A (G12).
- **Ops:** Sync `weekly.yml` + `safety.yaml` YOLO flags to `argus-runner`; paste Steward bootstrap once.

## 2026-11-05 — Ship v0.4.0 (YOLO + portfolio reports)

- **Decision:** Release hands-off YOLO, health/rate-limit, apply history, shareable reports, and Grok draft pack as **0.4.0**.
- **Gates:** `update-deps` + `verify` (96 tests); template Release Please / full pre-release-gate remain N/A (G12/G14).
- **Ops note:** Mass YOLO merges + runner CodeQL on history sync can exhaust free Actions minutes — thin runner CI on `argus-history/**` when needed.

## 2026-11-05 — Grok Bots draft/digest + optional YOLO

- **Decision:** Grok Bots = notice/draft/`argus-inbox` handoff only (no merge). Argus + Dependabot = sole mutators. Optional `apply_mode: yolo` auto-merges green gated/`auto_safe` (+ Dependabot patch) with hard floors intact.
- **Docs:** `docs/GROK_BOTS.md`, `docs/YOLO.md`, `docs/grok-bots/*`, ADR `docs/adr/0001-grok-bots-draft-digest-and-yolo.md`.
- **Prefer:** grow Argus `auto_safe` matchers over LLM code edits.

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
