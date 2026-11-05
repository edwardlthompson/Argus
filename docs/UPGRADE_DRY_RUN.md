# `/upgrade` dry-run against parent 1.12+

1. Compare `.template-version` to [agent-project-bootstrap releases](https://github.com/edwardlthompson/agent-project-bootstrap/releases).
2. Diff FOSS Cursor surface (commands/hooks/skills) — do **not** import full `scripts/lib` unless a BUILD_PLAN row says so.
3. Record gaps in `docs/PARENT_GAP_LIST.md`.
4. Apply only with `[HUMAN]` approval.
