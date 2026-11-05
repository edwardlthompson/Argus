# Third-party / family reports

Scan someone else’s repositories without changing anything:

```bash
argus report --target brother-username
argus report --target brother-username/some-repo
argus report --target some-org --public-only
```

## Guarantees

- `GitHubClient.report_only` is forced on
- No PRs, no settings changes, no agent dispatch writes
- HTML banner: “Read-only report — no changes were made.”

## Sharing the result

Send them `dist/report.html` (or publish it privately). The human task list uses Grandma Mode steps they can follow on their own account.
