# Upgrading from the parent template

Parent: [edwardlthompson/agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap)

1. Read the parent release notes for versions newer than `.template-version`.
2. Diff against this lean child — **do not** blindly copy `modules/`, `examples/`, or parent `scripts/lib/*` (G12).
3. Cursor FOSS surface (G13):
   - Re-copy `.cursor/commands/`, `.cursor/hooks/`, curated `.cursor/skills/`, `.cursor/agents/` from parent.
   - Re-apply Argus N/A banners (template-only commands) and daily supers prefaces.
   - Keep Argus `session_start_context.py` and subagent rewrites.
   - Run `python scripts/agent-run.py check-cursor-hooks --smoke`.
   - Any **unknown** `agent-run` verb (exit 2) → add to `VERIFY_VERBS` or `NA_VERBS` in `scripts/agent-run.py`.
4. Update `.template-version`, re-run the table in `docs/PARENT_GAP_LIST.md`, close or wont each new gap.
5. Run `scripts/verify.sh` / `scripts/verify.ps1` or `python scripts/agent-run.py verify`.

Interval preference lives in `.template-update.json` (`weekly` default).
