# Decision log

## 2026-11-04 — Parent/child lineage

- **Decision:** Treat Argus as a product child of `edwardlthompson/agent-project-bootstrap` v1.12.0, not a nested StarRupture app and not a full template fork.
- **Closed:** G01–G11 in `docs/PARENT_GAP_LIST.md` (lineage files, AGENTS adapters, community docs, Dependabot, checklist, spec/plan).
- **Wont:** G12–G15 (full agent-run runtime, Cursor plugin pack, modules/examples, CodeQL workflow) — keep verify.sh + GitHub defaults; revisit on `/upgrade`.
