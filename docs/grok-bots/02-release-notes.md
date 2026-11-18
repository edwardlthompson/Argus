# Skill — Release Notes

**Routine:** on-demand (“draft notes for REPO”) or tag/release notification. Not every merge.

```text
(Use shared preamble.)

Given repo + since-ref (previous tag or user-supplied): list up to 30 merged PR titles + numbers.
Group Feat / Fix / Docs / Other (Conventional Commit style when obvious).
Draft a release body suitable for GitHub Releases and an optional [Unreleased] CHANGELOG section.
Flag PRs that lack issue links.
Do not create a GitHub Release, tag, or version bump. Human publishes.
Stop after the draft.
```

CHANGELOG reformat: use [`08-changelog-helper.md`](08-changelog-helper.md) on the same Bot (do not dual-trigger on every tag).
