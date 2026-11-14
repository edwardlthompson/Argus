# News Inbox

Auto-collected inbox of news, upstream updates, security fixes, and ideas relevant to this repo, appended daily by News Bot.
A Cursor planning agent should review these items and fold the useful ones into BUILD_PLAN; entries are append-only, newest at the bottom.


## 2026-11-13

**News and updates**

- GitHub will pause Dependabot alerts on repos with no activity in the past year starting Dec 8, 2026; a push re-enables them. [source](https://github.blog/changelog/2026-11-10-dependabot-alerts-will-pause-on-inactive-repositories)
- Wave of npm malware posing as MCP/agent tools (e.g. karma365-mcp, @rclaude/darwin-arm64, helper-agent); advisories say treat machines as compromised. [source](https://github.com/advisories/GHSA-72xc-q3v8-7grp)
- Issue types and issue fields (Priority, Effort, dates) are now available on personal-account repos. [source](https://github.blog/changelog/2026-11-11-issue-types-and-fields-are-available-for-personal-accounts)
- Designing an autonomous development team: architect / implementor / reviewer agent roles with bounded review cycles. [source](https://sookocheff.com/post/ai/designing-an-autonomous-development-team/)

**Tasks for the planning agent**

- [ ] Flag repos at risk of Dependabot alert pause — Hygiene scoring should catch repos idle ~1 year before alerts silently stop on Dec 8. Label: `[AGENT][LOCAL]` · Priority: P1 · https://github.blog/changelog/2026-11-10-dependabot-alerts-will-pause-on-inactive-repositories
- [ ] Add a check for unpinned MCP/agent npm packages — Portfolio-wide detection of `npx -y` agent tooling reduces exposure to the current malware wave. Label: `[AGENT][LOCAL]` · Priority: P2 · https://github.com/advisories/GHSA-72xc-q3v8-7grp
- [ ] Evaluate issue types/fields for cross-repo triage — Native Priority/Effort fields could feed Argus scoring. Label: `[AGENT][LOCAL]` · Priority: P3 · https://github.blog/changelog/2026-11-11-issue-types-and-fields-are-available-for-personal-accounts
- [ ] Compare gated-agent flow with architect/implementor/reviewer roles — Ideas for bounding Argus's auto-apply review cycles. Label: `[AGENT][LOCAL]` · Priority: P3 · https://sookocheff.com/post/ai/designing-an-autonomous-development-team/

## 2026-11-14

**News and updates**

- wfx-loot campaign pushed a CI secret stealer into 17,000+ public repos using stolen GitHub credentials since Nov 10; an npm postinstall hook slipped past GitHub's workflow hold. IOCs: wfx-docs branch, .ci-xxxxxx.sh files, build-audit-*.yml workflows. [source](https://blog.gitguardian.com/wfx-loot-a-ci-secret-stealer-pushed-with-stolen-github-credentials/)
- Stack Overflow blog: 'Your coding agent shouldn't grade its own homework' — only 9.6% of 1,000 AI-written tests were useful; argues for an independent fresh-context QA agent. [source](https://stackoverflow.blog/2026/11/13/your-coding-agent-shouldn-t-grade-its-own-homework/)

**Tasks for the planning agent**

- [ ] Audit the repo for wfx-loot IOCs — Checks for the wfx-docs branch/PR, .ci-*.sh files, build-audit-*.yml workflows and new npm lifecycle hooks, since the campaign steals CI secrets and Cursor credentials. Label: `[AGENT][LOCAL]` · Priority: P1 · https://blog.gitguardian.com/wfx-loot-a-ci-secret-stealer-pushed-with-stolen-github-credentials/
- [ ] Add a fleet rule flagging wfx-loot IOCs and new npm lifecycle hooks — The IOCs are deterministic, so the portfolio scanner can catch them automatically across every repo. Label: `[AGENT][LOCAL]` · Priority: P2 · https://blog.gitguardian.com/wfx-loot-a-ci-secret-stealer-pushed-with-stolen-github-credentials/
- [ ] Add an independent-verifier step to /verify — A fresh-context reviewer that cannot edit tests catches what the coding agent's own tests miss. Label: `[AGENT][LOCAL]` · Priority: P3 · https://stackoverflow.blog/2026/11/13/your-coding-agent-shouldn-t-grade-its-own-homework/
