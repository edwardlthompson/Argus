# Skill — Stale PR Nudge

**Routine:** weekly (e.g. Monday).

```text
(Use shared preamble.)

List open PRs on the allowlist older than 7 days without review/activity. Cap 20.
Metadata only: title, age, author, URL. Do not read diffs.
Output one markdown table for Slack/chat.
Do not post PR comments unless the human says “post it” for a specific row.
Do not merge or close human-authored PRs. Closing abandoned bot PRs is Argus/GitHub policy, not this skill.
Stop after the table.
```
