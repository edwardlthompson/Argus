# Upgrading from the parent template

Parent: [edwardlthompson/agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap)

1. Read the parent release notes for versions newer than `.template-version`.
2. Diff against this lean child — **do not** blindly copy `modules/`, `examples/`, or the full `scripts/agent-run.py` surface unless a BUILD_PLAN row asks for it.
3. Update `.template-version`, re-run the table in `docs/PARENT_GAP_LIST.md`, close or wont each new gap.
4. Run `scripts/verify.sh` / `scripts/verify.ps1`.

Interval preference lives in `.template-update.json` (`weekly` default).
