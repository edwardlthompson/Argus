# Skill — Triage / Repro

**Routine:** issue labeled `needs-repro` on allowlisted product repos only. Ignore unlabeled issues.

```text
(Use shared preamble.)

Only act when the issue has label needs-repro.
Read the issue body and any linked stack traces. Read README/docs paths named in the issue only.
Attempt a minimal repro at most once. If blocked, document the blocker.
Post one Issue comment with: Repro steps, Expected, Actual, Environment, Minimal test idea, optional screenshot note.
Never push branches, edit code, or open PRs.

If YOLO handoff requested: add/update an argus-inbox Issue with kind needs-repro and link back to this issue. Argus owns any agent attempt.
Stop after the comment (and optional handoff).
```

Product repos should document the `needs-repro` label in CONTRIBUTING (operator apps; not required in Argus core).
