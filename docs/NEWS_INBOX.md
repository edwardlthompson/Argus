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

- [x] Flag repos at risk of Dependabot alert pause — Hygiene scoring should catch repos idle ~1 year before alerts silently stop on Dec 8. Label: `[AGENT][LOCAL]` · Priority: P1 · https://github.blog/changelog/2026-11-10-dependabot-alerts-will-pause-on-inactive-repositories (synced to BUILD_PLAN)
- [x] Add a check for unpinned MCP/agent npm packages — Portfolio-wide detection of `npx -y` agent tooling reduces exposure to the current malware wave. Label: `[AGENT][LOCAL]` · Priority: P2 · https://github.com/advisories/GHSA-72xc-q3v8-7grp (synced to BUILD_PLAN)
- [ ] Evaluate issue types/fields for cross-repo triage — Native Priority/Effort fields could feed Argus scoring. Label: `[AGENT][LOCAL]` · Priority: P3 · https://github.blog/changelog/2026-11-11-issue-types-and-fields-are-available-for-personal-accounts
- [ ] Compare gated-agent flow with architect/implementor/reviewer roles — Ideas for bounding Argus's auto-apply review cycles. Label: `[AGENT][LOCAL]` · Priority: P3 · https://sookocheff.com/post/ai/designing-an-autonomous-development-team/

## 2026-11-14

**News and updates**

- wfx-loot campaign pushed a CI secret stealer into 17,000+ public repos using stolen GitHub credentials since Nov 10; an npm postinstall hook slipped past GitHub's workflow hold. IOCs: wfx-docs branch, .ci-xxxxxx.sh files, build-audit-*.yml workflows. [source](https://blog.gitguardian.com/wfx-loot-a-ci-secret-stealer-pushed-with-stolen-github-credentials/)
- Stack Overflow blog: 'Your coding agent shouldn't grade its own homework' — only 9.6% of 1,000 AI-written tests were useful; argues for an independent fresh-context QA agent. [source](https://stackoverflow.blog/2026/11/13/your-coding-agent-shouldn-t-grade-its-own-homework/)

**Tasks for the planning agent**

- [x] Audit the repo for wfx-loot IOCs — Checks for the wfx-docs branch/PR, .ci-*.sh files, build-audit-*.yml workflows and new npm lifecycle hooks, since the campaign steals CI secrets and Cursor credentials. Label: `[AGENT][LOCAL]` · Priority: P1 · https://blog.gitguardian.com/wfx-loot-a-ci-secret-stealer-pushed-with-stolen-github-credentials/ (synced to BUILD_PLAN)
- [x] Add a fleet rule flagging wfx-loot IOCs and new npm lifecycle hooks — The IOCs are deterministic, so the portfolio scanner can catch them automatically across every repo. Label: `[AGENT][LOCAL]` · Priority: P2 · https://blog.gitguardian.com/wfx-loot-a-ci-secret-stealer-pushed-with-stolen-github-credentials/ (synced to BUILD_PLAN)
- [ ] Add an independent-verifier step to /verify — A fresh-context reviewer that cannot edit tests catches what the coding agent's own tests miss. Label: `[AGENT][LOCAL]` · Priority: P3 · https://stackoverflow.blog/2026/11/13/your-coding-agent-shouldn-t-grade-its-own-homework/

## 2026-11-15

**News and updates**

- Cursor traced its Oct 29 incident to a vendor-exposed key: attackers copied some non-Privacy-Mode agent traces (some with pasted credentials) and briefly planted a backdoored Claude Code extension (2.1.312/2.1.313); contained since Nov 1. [source](https://cursor.com/blog/security-incident-update) · [IOCs](https://cursor.com/blog/claude-code-extension-security-notice)
- More agent-CLI lures flagged as npm malware: @claudecode/cli and zread CLI (all platform packages); treat any machine that installed them as compromised. [source](https://github.com/advisories/GHSA-vp2q-gp5r-xh5j) · [zread](https://github.com/advisories/GHSA-3429-mj25-c5wf)

**Tasks for the planning agent**

- [x] Propagate a "never paste secrets into agent chats" AGENTS.md rule to child repos — Cursor's incident showed credentials pasted into agent traces can be stolen and reused, so the fleet contract should forbid it. Label: `[AGENT][LOCAL]` · Priority: P2 · https://cursor.com/blog/security-incident-update (synced to BUILD_PLAN)
- [ ] Add @claudecode/cli, zread_cli and @zread/cli-* to the agent-package denylist check — The portfolio scanner can flag these new agent-lure malware packages wherever they appear. Label: `[AGENT][LOCAL]` · Priority: P3 · https://github.com/advisories/GHSA-vp2q-gp5r-xh5j

## 2026-11-16

**News and updates**

- GitHub Actions will block `pull_request_target` runs in public repos by default from Dec 2 unless an Actions event policy allows them; today (Nov 16) 12:00–14:00 AST is the second brownout. [source](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/)
- Git 2.56.1 (Nov 10) fixes 6 vulnerabilities, including code execution on recursive clone (CVE-2026-111760); backports 2.55.1–2.50.2 and Git for Windows 2.56.1 shipped the same day; GitHub is patching hosted runners. [source](https://github.blog/open-source/git/git-security-vulnerabilities-announced-7/)
- Google Antigravity 2.32.0 adds Dynamic Workflows: a reviewable, saved Python script fans work out to sub-agents that return JSON-Schema-checked results (SDK 0.1.22 `beta.workflows`). [source](https://antigravity.google/docs/dynamic-workflows/) · [changelog](https://antigravity.google/docs/changelog)

**Tasks for the planning agent**

- [x] Add a hygiene rule that flags `on: pull_request_target` in public repo workflows — GitHub blocks these runs by default from Dec 2, so the fleet scan should catch any use (and any that sneak back in) and point to the pull_request fix. Label: `[AGENT][LOCAL]` · Priority: P2 · https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/ (synced to BUILD_PLAN)
- [x] Update Git to 2.56.1+ on dev PCs and WSL, and have Argus flag hosts below the patched version — A recursive clone of a hostile repo can run code on unpatched Git, and Argus clones many repos. Label: `[HUMAN][PC]` · Priority: P2 · https://github.blog/open-source/git/git-security-vulnerabilities-announced-7/ (synced to BUILD_PLAN)
- [ ] Consider a saved, schema-bound fan-out script for per-repo gated agents — Antigravity's reviewable workflow pattern could bound Argus's per-repo agent runs with checked JSON results. Label: `[AGENT][LOCAL]` · Priority: P3 · https://antigravity.google/docs/dynamic-workflows/

## 2026-11-18

Catch-up for Nov 17–18 (the daily brief did not run those mornings).

**News and updates**

- Both `pull_request_target` brownouts (Nov 9 and Nov 16) have passed, and MultiAppShare-'s `.github/workflows/pr-title.yml` still uses `pull_request_target`. The default block becomes permanent on Dec 2. [source](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/)
- Unauthorized PyPI releases 1.26.1 and 1.26.2 of Microsoft's `agent-framework` (Nov 17, now removed) dropped a `.pth` hook that stole env secrets, credential files, and Azure/GitHub OIDC tokens on every Python start. Pin to 1.26.0 or don't install it; treat any hit as compromised. [source](https://www.wiz.io/blog/malicious-version-of-microsofts-agent-framework-published-to-pypi) · [uv 0.13.9](https://github.com/astral-sh/uv/releases/tag/0.13.9) rejects wheels advertised under a different package name.

**Tasks for the planning agent**

- [x] Add a fleet check for agent-framework 1.26.1/1.26.2 and unexpected .pth startup hooks — The malicious wheels ran a credential stealer on every Python start, and Argus should flag this package and stray site-packages hooks across the fleet. Label: `[AGENT][LOCAL]` · Priority: P2 · https://www.wiz.io/blog/malicious-version-of-microsofts-agent-framework-published-to-pypi (synced to BUILD_PLAN)

## 2026-11-19

**News and updates**

- Update on the agent-framework PyPI compromise: Wiz ties the malicious uploads to a stolen Microsoft ESRP release-signing certificate, and a same-day PyPI account was listed on 14 Microsoft projects (including Semantic Kernel and AutoGen). The bad wheels were live 39 minutes (427 downloads); 1.26.2 also requested GitHub Actions/Azure OIDC tokens, so treat them as exposed for workflows with `id-token: write`. No repo here depends on semantic-kernel or autogen; the existing P2s still apply. [source](https://sxz.io/microsoft-agent-framework-pypi-credential-stealer-esrp-certificate-14-projects/)
- microsoft/onnxruntime and related repos went private (404) on Nov 17 during a malicious-content investigation, a live example of a dependency's source, tags and release assets vanishing without notice. [audit write-up](https://dev.to/karmabox/microsoftonnxruntime-is-404-here-is-the-audit-we-ran-on-our-own-pipeline-1530)
- GitHub CLI v2.105.0 adds `gh event listen` (preview, needs the Event Streams waitlist): it waits for PR events such as reviews, head changes, conflicts and completed check suites instead of polling. [source](https://github.blog/changelog/2026-11-18-wait-for-pull-request-events-with-github-cli)

**Tasks for the planning agent**

- [ ] When finishing the open agent-framework fleet check, also flag any Microsoft-published PyPI package (semantic-kernel, autogen-*, agent-framework-*) with a release after 2026-11-17 — the signing path was compromised, not just one package, until Microsoft closes the investigation. Label: `[AGENT][LOCAL]` · Priority: P3 · https://sxz.io/microsoft-agent-framework-pypi-credential-stealer-esrp-certificate-14-projects/
- [ ] Add an Argus lineage signal for fleet repos whose workflows/scripts fetch GitHub repos or release URLs that now return 404 (`uses:` actions, `releases/download` URLs, submodules) — a vanished upstream breaks builds silently, and Argus already scores lineage. Label: `[AGENT][LOCAL]` · Priority: P3 · https://dev.to/karmabox/microsoftonnxruntime-is-404-here-is-the-audit-we-ran-on-our-own-pipeline-1530
- [ ] Prototype an event-driven wait for Dependabot/YOLO merges with `gh event listen --timeout`, falling back to the check-runs poll loop — fewer API calls and less runner time, and Actions minutes run out fast. Label: `[AGENT][LOCAL]` · Priority: P3 · https://github.blog/changelog/2026-11-18-wait-for-pull-request-events-with-github-cli
