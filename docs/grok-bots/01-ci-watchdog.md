# Skill — CI Watchdog

**Routine:** weekdays ~09:00 local (or on allowlisted workflow failure — never org-wide).

```text
(Use shared preamble.)

List failed GitHub Actions runs on the allowlist in the last 24h.
For each failure: repo, workflow, job, conclusion, link, and ≤3 bullet cause guesses from the last ≤80 log lines only.
Skip repos with zero failures.
Output one markdown digest table. Title suggestion: ci-digest YYYY-MM-DD.

If apply_mode is yolo (operator said so) OR they ask to hand off: open/update one private argus-inbox Issue using the handoff format in docs/GROK_BOTS.md. Do not open fix PRs. Do not re-run workflows.
Stop after the digest (and optional single handoff).
```
