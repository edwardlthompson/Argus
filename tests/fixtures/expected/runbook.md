# Argus Runbook

Generated for 10 repositories.

## example/parked-lab

**Attention:** 16.6/100 (medium confidence)
_Notes:_ missing categories: lineage; hygiene/security-only scoring for parked/archived

### Human tasks

#### H1. Decide whether to archive this parked repository

**Why:** Parked repos that stay public forever confuse visitors about what is maintained.

1. Open the repository on GitHub.
2. Read the README and decide: keep it visible, or archive it.
3. If archiving: Settings → scroll to **Danger Zone** → **Archive this repository**.
4. If keeping: reply on the Argus report that it should stay parked.

**Done when:** Repo is archived, or you noted 'keep parked' on the Argus report

### Agent prompt for `example/parked-lab`

Paste this entire block into your coding agent. Stop if any GATE fails twice.

```text
Repository: example/parked-lab
You are performing gated Argus hygiene/correctness work.
Prefer opening a PR over committing to the default branch.

## Phase 2

> unverified — check before pasting

### SEC-CODEQL: Turn on CodeQL / default code scanning
Static analysis catches common security bugs before they ship.
Enable GitHub Code Scanning default setup (CodeQL) via the repository API.
Do not invent custom query packs. Stop after two gate failures.

GATE: Code scanning shows as configured

## Phase final — verify & PR

1. Run project tests / verify script if present.
2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: SEC-CODEQL
3. Push branch `chore/argus-agent` (or continue the existing Argus branch).
4. Open a Pull Request whose body lists the fix IDs above.

GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED
```

### Auto-safe (controller may open PRs)

- `HYGIENE-TOPICS` — Set 3–5 specific repository topics — GATE: `true`
- `HYGIENE-SECURITY-MD` — Add SECURITY.md — GATE: `test -f SECURITY.md`
- `HYGIENE-CODEOWNERS` — Add CODEOWNERS — GATE: `test -f CODEOWNERS -o -f .github/CODEOWNERS -o -f docs/CODEOWNERS`
- `HYGIENE-GITIGNORE` — Add a starter .gitignore — GATE: `test -f .gitignore`
- `SEC-CODEQL-WORKFLOW` — Add CodeQL workflow pack — GATE: `test -f .github/workflows/codeql.yml -o -f .github/workflows/codeql.yaml`

## example/active-rotting

**Attention:** needs human read (low confidence) — raw score 89.3/100
_Notes:_ missing categories: lineage, prs, releases

### Human tasks

#### H1. Park or archive a long-inactive active repo

**Why:** Repos that look abandoned confuse visitors about what you still maintain.

1. Open the repository on GitHub.
2. Decide: keep active, park (tell Argus), or archive.
3. To archive: Settings → Danger Zone → Archive this repository.
4. To park without archiving: ask Argus `argus park owner/repo`.

**Done when:** Repo is parked, archived, or you noted keep-active on the report

### Agent prompt for `example/active-rotting`

Paste this entire block into your coding agent. Stop if any GATE fails twice.

```text
Repository: example/active-rotting
You are performing gated Argus hygiene/correctness work.
Prefer opening a PR over committing to the default branch.

## Phase 2

### AGENT-STALE-ISSUES: Triage truly stale issues
Ancient open issues hide real bugs and signal abandonment.
For Issues idle ≥90 days: close if patterned (argus-auto / bot digest); otherwise
nudge once. Do not close human product bugs — ask for needs-human instead.

### ISSUE-PATTERNED-AUTO: Close patterned bot / argus-auto Issues
Digest, Dependabot-noise, and Issues labeled argus-auto are mechanical — continuous zero closes them; human product bugs stay open.

Close Issues labeled argus-auto / argus:auto, Argus digest titles, or bot Issues
matching bump/upgrade/chore(argus) patterns. Do not close human product bugs.

> unverified — check before pasting

### SEC-CODEQL: Turn on CodeQL / default code scanning
Static analysis catches common security bugs before they ship.
Enable GitHub Code Scanning default setup (CodeQL) via the repository API.
Do not invent custom query packs. Stop after two gate failures.

GATE: Code scanning shows as configured

## Phase 3

### AGENT-MEMORY-LAYOUT: Move agent memory/log files into .agent/
Agent scratch files in the repo root confuse contributors and tools.
Search for agent memory/log files (AGENT_MEMORY.md at root, .cursorrules duplicates,
loose session dumps). Move durable notes into `.agent/` and update references.
Do not delete history — relocate only.

> unverified — check before pasting

### AGENT-PRESENTATION: Presentation polish requiring judgment
Descriptions, badges, and README structure need a careful human-like edit.
If README is missing, create a short accurate README (purpose, quick start, what it is not).
If description is empty, propose a ≤120 character description in the PR body for a human to paste.

GATE: test -f README.md

## Phase final — verify & PR

1. Run project tests / verify script if present.
2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: AGENT-STALE-ISSUES, ISSUE-PATTERNED-AUTO, SEC-CODEQL, AGENT-MEMORY-LAYOUT, AGENT-PRESENTATION
3. Push branch `chore/argus-agent` (or continue the existing Argus branch).
4. Open a Pull Request whose body lists the fix IDs above.

GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED
```

### Auto-safe (controller may open PRs)

- `HYGIENE-GITATTRIBUTES` — Add language attribution (.gitattributes) — GATE: `test -f .gitattributes`
- `HYGIENE-TOPICS` — Set 3–5 specific repository topics — GATE: `true`
- `HYGIENE-LICENSE` — Ensure LICENSE file is present — GATE: `test -f LICENSE -o -f LICENSE.md`
- `HYGIENE-SECURITY-MD` — Add SECURITY.md — GATE: `test -f SECURITY.md`
- `HYGIENE-CONTRIBUTING` — Add CONTRIBUTING.md — GATE: `test -f CONTRIBUTING.md`
- `HYGIENE-COC` — Add CODE_OF_CONDUCT.md — GATE: `test -f CODE_OF_CONDUCT.md`
- `HYGIENE-CI` — Add a basic CI workflow on the default branch — GATE: `test -d .github/workflows && ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null | head -1 | grep -q .`
- `HYGIENE-CODEOWNERS` — Add CODEOWNERS — GATE: `test -f CODEOWNERS -o -f .github/CODEOWNERS -o -f docs/CODEOWNERS`
- `HYGIENE-GITIGNORE` — Add a starter .gitignore — GATE: `test -f .gitignore`
- `SEC-CODEQL-WORKFLOW` — Add CodeQL workflow pack — GATE: `test -f .github/workflows/codeql.yml -o -f .github/workflows/codeql.yaml`
- `SEC-DEPENDABOT-ENABLE` — Enable Dependabot alerts via API — GATE: `true`
- `SEC-SECRET-SCAN-ENABLE` — Enable secret scanning + push protection via API — GATE: `true`

## example/forked-tool

**Attention:** needs human read (low confidence) — raw score 15.4/100
_Notes:_ missing categories: lineage, prs, releases

### Agent prompt for `example/forked-tool`

Paste this entire block into your coding agent. Stop if any GATE fails twice.

```text
Repository: example/forked-tool
You are performing gated Argus hygiene/correctness work.
Prefer opening a PR over committing to the default branch.

## Phase 2

> unverified — check before pasting

### SEC-CODEQL: Turn on CodeQL / default code scanning
Static analysis catches common security bugs before they ship.
Enable GitHub Code Scanning default setup (CodeQL) via the repository API.
Do not invent custom query packs. Stop after two gate failures.

GATE: Code scanning shows as configured

## Phase 3

> unverified — check before pasting

### AGENT-WHAT-NOT: Add or improve a "What this is not" section
Clear non-goals prevent wrong expectations and support tickets.
In README.md, ensure a short "## What this is not" section with 3–5 concrete bullets.
Keep tone plain. Do not invent features.

GATE: grep -qi 'what this is not' README.md

## Phase final — verify & PR

1. Run project tests / verify script if present.
2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: SEC-CODEQL, AGENT-WHAT-NOT
3. Push branch `chore/argus-agent` (or continue the existing Argus branch).
4. Open a Pull Request whose body lists the fix IDs above.

GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED
```

### Auto-safe (controller may open PRs)

- `HYGIENE-CODEOWNERS` — Add CODEOWNERS — GATE: `test -f CODEOWNERS -o -f .github/CODEOWNERS -o -f docs/CODEOWNERS`
- `HYGIENE-GITIGNORE` — Add a starter .gitignore — GATE: `test -f .gitignore`
- `SEC-CODEQL-WORKFLOW` — Add CodeQL workflow pack — GATE: `test -f .github/workflows/codeql.yml -o -f .github/workflows/codeql.yaml`

## example/docs-only

**Attention:** needs human read (low confidence) — raw score 17.4/100
_Notes:_ missing categories: lineage, prs, releases

### Agent prompt for `example/docs-only`

Paste this entire block into your coding agent. Stop if any GATE fails twice.

```text
Repository: example/docs-only
You are performing gated Argus hygiene/correctness work.
Prefer opening a PR over committing to the default branch.

## Phase 2

### ISSUE-PATTERNED-AUTO: Close patterned bot / argus-auto Issues
Digest, Dependabot-noise, and Issues labeled argus-auto are mechanical — continuous zero closes them; human product bugs stay open.

Close Issues labeled argus-auto / argus:auto, Argus digest titles, or bot Issues
matching bump/upgrade/chore(argus) patterns. Do not close human product bugs.

> unverified — check before pasting

### SEC-CODEQL: Turn on CodeQL / default code scanning
Static analysis catches common security bugs before they ship.
Enable GitHub Code Scanning default setup (CodeQL) via the repository API.
Do not invent custom query packs. Stop after two gate failures.

GATE: Code scanning shows as configured

## Phase 3

> unverified — check before pasting

### AGENT-WHAT-NOT: Add or improve a "What this is not" section
Clear non-goals prevent wrong expectations and support tickets.
In README.md, ensure a short "## What this is not" section with 3–5 concrete bullets.
Keep tone plain. Do not invent features.

GATE: grep -qi 'what this is not' README.md

## Phase final — verify & PR

1. Run project tests / verify script if present.
2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: ISSUE-PATTERNED-AUTO, SEC-CODEQL, AGENT-WHAT-NOT
3. Push branch `chore/argus-agent` (or continue the existing Argus branch).
4. Open a Pull Request whose body lists the fix IDs above.

GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED
```

### Auto-safe (controller may open PRs)

- `HYGIENE-GITATTRIBUTES` — Add language attribution (.gitattributes) — GATE: `test -f .gitattributes`
- `HYGIENE-CODEOWNERS` — Add CODEOWNERS — GATE: `test -f CODEOWNERS -o -f .github/CODEOWNERS -o -f docs/CODEOWNERS`
- `HYGIENE-GITIGNORE` — Add a starter .gitignore — GATE: `test -f .gitignore`
- `SEC-CODEQL-WORKFLOW` — Add CodeQL workflow pack — GATE: `test -f .github/workflows/codeql.yml -o -f .github/workflows/codeql.yaml`

## example/human-only

**Attention:** 5.1/100 (medium confidence)
_Notes:_ missing categories: lineage; hygiene/security-only scoring for parked/archived

### Human tasks

#### H1. Decide whether to archive this parked repository

**Why:** Parked repos that stay public forever confuse visitors about what is maintained.

1. Open the repository on GitHub.
2. Read the README and decide: keep it visible, or archive it.
3. If archiving: Settings → scroll to **Danger Zone** → **Archive this repository**.
4. If keeping: reply on the Argus report that it should stay parked.

**Done when:** Repo is archived, or you noted 'keep parked' on the Argus report

## example/agent-only

**Attention:** 29.1/100 (medium confidence)
_Notes:_ missing categories: releases

### Agent prompt for `example/agent-only`

Paste this entire block into your coding agent. Stop if any GATE fails twice.

```text
Repository: example/agent-only
You are performing gated Argus hygiene/correctness work.
Prefer opening a PR over committing to the default branch.

## Phase 2

### AGENT-STALE-ISSUES: Triage truly stale issues
Ancient open issues hide real bugs and signal abandonment.
For Issues idle ≥90 days: close if patterned (argus-auto / bot digest); otherwise
nudge once. Do not close human product bugs — ask for needs-human instead.

### CI-LATEST-FAILED: Fix failing CI on the default branch
A red default-branch build means the project cannot be trusted to ship.
Open the latest failed Actions run on the default branch. Fix the clear failure.
Do not disable the workflow. Stop after two gate failures.

### ISSUE-PATTERNED-AUTO: Close patterned bot / argus-auto Issues
Digest, Dependabot-noise, and Issues labeled argus-auto are mechanical — continuous zero closes them; human product bugs stay open.

Close Issues labeled argus-auto / argus:auto, Argus digest titles, or bot Issues
matching bump/upgrade/chore(argus) patterns. Do not close human product bugs.

### PR-STALE: Triage stale open pull requests
Old PRs hide real review work and confuse contributors.
For each open PR idle ≥30 days: comment with status, close if obsolete, or label needs-human.
Prefer not force-merging.

GATE: true

## Phase 3

### AGENT-MEMORY-LAYOUT: Move agent memory/log files into .agent/
Agent scratch files in the repo root confuse contributors and tools.
Search for agent memory/log files (AGENT_MEMORY.md at root, .cursorrules duplicates,
loose session dumps). Move durable notes into `.agent/` and update references.
Do not delete history — relocate only.

> unverified — check before pasting

### AGENT-WHAT-NOT: Add or improve a "What this is not" section
Clear non-goals prevent wrong expectations and support tickets.
In README.md, ensure a short "## What this is not" section with 3–5 concrete bullets.
Keep tone plain. Do not invent features.

GATE: grep -qi 'what this is not' README.md

## Phase 4

### LINEAGE-RECOMMEND-UPGRADE: Open parent template lineage bump PR
A version gap needs a gated lineage bump; continuous zero opens the PR via handler.
Open or refresh the Argus lineage bump PR so .template-version matches the parent pin.
Do not invent sacred-file rewrites; follow docs/UPGRADING_FROM_TEMPLATE.md.
Stop after two gate failures.

GATE: Child .template-version equals parent expected_version

## Phase final — verify & PR

1. Run project tests / verify script if present.
2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: AGENT-STALE-ISSUES, CI-LATEST-FAILED, ISSUE-PATTERNED-AUTO, PR-STALE, AGENT-MEMORY-LAYOUT, AGENT-WHAT-NOT, LINEAGE-RECOMMEND-UPGRADE
3. Push branch `chore/argus-agent` (or continue the existing Argus branch).
4. Open a Pull Request whose body lists the fix IDs above.

GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED
```

### Auto-safe (controller may open PRs)

- `HYGIENE-CODEOWNERS` — Add CODEOWNERS — GATE: `test -f CODEOWNERS -o -f .github/CODEOWNERS -o -f docs/CODEOWNERS`
- `HYGIENE-GITIGNORE` — Add a starter .gitignore — GATE: `test -f .gitignore`
- `LINEAGE-VERSION-STALE` — Bump .template-version toward parent — GATE: `test -f .template-version`

## example/low-confidence

**Attention:** needs human read (low confidence) — raw score 52.5/100
_Notes:_ missing categories: ci, deps, lineage, presentation, prs, releases, responsiveness, security

### Agent prompt for `example/low-confidence`

Paste this entire block into your coding agent. Stop if any GATE fails twice.

```text
Repository: example/low-confidence
You are performing gated Argus hygiene/correctness work.
Prefer opening a PR over committing to the default branch.

## Phase 2

### ISSUE-PATTERNED-AUTO: Close patterned bot / argus-auto Issues
Digest, Dependabot-noise, and Issues labeled argus-auto are mechanical — continuous zero closes them; human product bugs stay open.

Close Issues labeled argus-auto / argus:auto, Argus digest titles, or bot Issues
matching bump/upgrade/chore(argus) patterns. Do not close human product bugs.

> unverified — check before pasting

### SEC-CODEQL: Turn on CodeQL / default code scanning
Static analysis catches common security bugs before they ship.
Enable GitHub Code Scanning default setup (CodeQL) via the repository API.
Do not invent custom query packs. Stop after two gate failures.

GATE: Code scanning shows as configured

## Phase 3

> unverified — check before pasting

### AGENT-PRESENTATION: Presentation polish requiring judgment
Descriptions, badges, and README structure need a careful human-like edit.
If README is missing, create a short accurate README (purpose, quick start, what it is not).
If description is empty, propose a ≤120 character description in the PR body for a human to paste.

GATE: test -f README.md

## Phase final — verify & PR

1. Run project tests / verify script if present.
2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: ISSUE-PATTERNED-AUTO, SEC-CODEQL, AGENT-PRESENTATION
3. Push branch `chore/argus-agent` (or continue the existing Argus branch).
4. Open a Pull Request whose body lists the fix IDs above.

GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED
```

### Auto-safe (controller may open PRs)

- `HYGIENE-GITATTRIBUTES` — Add language attribution (.gitattributes) — GATE: `test -f .gitattributes`
- `HYGIENE-TOPICS` — Set 3–5 specific repository topics — GATE: `true`
- `HYGIENE-SECURITY-MD` — Add SECURITY.md — GATE: `test -f SECURITY.md`
- `HYGIENE-CONTRIBUTING` — Add CONTRIBUTING.md — GATE: `test -f CONTRIBUTING.md`
- `HYGIENE-COC` — Add CODE_OF_CONDUCT.md — GATE: `test -f CODE_OF_CONDUCT.md`
- `HYGIENE-CI` — Add a basic CI workflow on the default branch — GATE: `test -d .github/workflows && ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null | head -1 | grep -q .`
- `HYGIENE-CODEOWNERS` — Add CODEOWNERS — GATE: `test -f CODEOWNERS -o -f .github/CODEOWNERS -o -f docs/CODEOWNERS`
- `HYGIENE-GITIGNORE` — Add a starter .gitignore — GATE: `test -f .gitignore`
- `SEC-CODEQL-WORKFLOW` — Add CodeQL workflow pack — GATE: `test -f .github/workflows/codeql.yml -o -f .github/workflows/codeql.yaml`
- `SEC-DEPENDABOT-ENABLE` — Enable Dependabot alerts via API — GATE: `true`
- `SEC-SECRET-SCAN-ENABLE` — Enable secret scanning + push protection via API — GATE: `true`

## brother/family-app

**Attention:** needs human read (low confidence) — raw score 66.5/100
_Notes:_ missing categories: lineage, prs, releases

### Agent prompt for `brother/family-app`

Paste this entire block into your coding agent. Stop if any GATE fails twice.

```text
Repository: brother/family-app
You are performing gated Argus hygiene/correctness work.
Prefer opening a PR over committing to the default branch.

## Phase 2

### ISSUE-PATTERNED-AUTO: Close patterned bot / argus-auto Issues
Digest, Dependabot-noise, and Issues labeled argus-auto are mechanical — continuous zero closes them; human product bugs stay open.

Close Issues labeled argus-auto / argus:auto, Argus digest titles, or bot Issues
matching bump/upgrade/chore(argus) patterns. Do not close human product bugs.

> unverified — check before pasting

### SEC-CODEQL: Turn on CodeQL / default code scanning
Static analysis catches common security bugs before they ship.
Enable GitHub Code Scanning default setup (CodeQL) via the repository API.
Do not invent custom query packs. Stop after two gate failures.

GATE: Code scanning shows as configured

## Phase 3

> unverified — check before pasting

### AGENT-WHAT-NOT: Add or improve a "What this is not" section
Clear non-goals prevent wrong expectations and support tickets.
In README.md, ensure a short "## What this is not" section with 3–5 concrete bullets.
Keep tone plain. Do not invent features.

GATE: grep -qi 'what this is not' README.md

## Phase final — verify & PR

1. Run project tests / verify script if present.
2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: ISSUE-PATTERNED-AUTO, SEC-CODEQL, AGENT-WHAT-NOT
3. Push branch `chore/argus-agent` (or continue the existing Argus branch).
4. Open a Pull Request whose body lists the fix IDs above.

GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED
```

### Auto-safe (controller may open PRs)

- `HYGIENE-GITATTRIBUTES` — Add language attribution (.gitattributes) — GATE: `test -f .gitattributes`
- `HYGIENE-TOPICS` — Set 3–5 specific repository topics — GATE: `true`
- `HYGIENE-LICENSE` — Ensure LICENSE file is present — GATE: `test -f LICENSE -o -f LICENSE.md`
- `HYGIENE-SECURITY-MD` — Add SECURITY.md — GATE: `test -f SECURITY.md`
- `HYGIENE-CONTRIBUTING` — Add CONTRIBUTING.md — GATE: `test -f CONTRIBUTING.md`
- `HYGIENE-COC` — Add CODE_OF_CONDUCT.md — GATE: `test -f CODE_OF_CONDUCT.md`
- `HYGIENE-CI` — Add a basic CI workflow on the default branch — GATE: `test -d .github/workflows && ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null | head -1 | grep -q .`
- `HYGIENE-CODEOWNERS` — Add CODEOWNERS — GATE: `test -f CODEOWNERS -o -f .github/CODEOWNERS -o -f docs/CODEOWNERS`
- `HYGIENE-GITIGNORE` — Add a starter .gitignore — GATE: `test -f .gitignore`
- `SEC-CODEQL-WORKFLOW` — Add CodeQL workflow pack — GATE: `test -f .github/workflows/codeql.yml -o -f .github/workflows/codeql.yaml`
- `SEC-DEPENDABOT-ENABLE` — Enable Dependabot alerts via API — GATE: `true`
- `SEC-SECRET-SCAN-ENABLE` — Enable secret scanning + push protection via API — GATE: `true`

## example/archived-old

**Attention:** 6.7/100 (high confidence)
_Notes:_ hygiene/security-only scoring for parked/archived

### Agent prompt for `example/archived-old`

Paste this entire block into your coding agent. Stop if any GATE fails twice.

```text
Repository: example/archived-old
You are performing gated Argus hygiene/correctness work.
Prefer opening a PR over committing to the default branch.

## Phase 2

> unverified — check before pasting

### SEC-CODEQL: Turn on CodeQL / default code scanning
Static analysis catches common security bugs before they ship.
Enable GitHub Code Scanning default setup (CodeQL) via the repository API.
Do not invent custom query packs. Stop after two gate failures.

GATE: Code scanning shows as configured

## Phase final — verify & PR

1. Run project tests / verify script if present.
2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: SEC-CODEQL
3. Push branch `chore/argus-agent` (or continue the existing Argus branch).
4. Open a Pull Request whose body lists the fix IDs above.

GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED
```

### Auto-safe (controller may open PRs)

- `HYGIENE-CODEOWNERS` — Add CODEOWNERS — GATE: `test -f CODEOWNERS -o -f .github/CODEOWNERS -o -f docs/CODEOWNERS`
- `HYGIENE-GITIGNORE` — Add a starter .gitignore — GATE: `test -f .gitignore`
- `SEC-CODEQL-WORKFLOW` — Add CodeQL workflow pack — GATE: `test -f .github/workflows/codeql.yml -o -f .github/workflows/codeql.yaml`

## example/experimental-spike

**Attention:** needs human read (low confidence) — raw score 50.8/100
_Notes:_ missing categories: lineage, prs, releases

### Agent prompt for `example/experimental-spike`

Paste this entire block into your coding agent. Stop if any GATE fails twice.

```text
Repository: example/experimental-spike
You are performing gated Argus hygiene/correctness work.
Prefer opening a PR over committing to the default branch.

## Phase 2

> unverified — check before pasting

### SEC-CODEQL: Turn on CodeQL / default code scanning
Static analysis catches common security bugs before they ship.
Enable GitHub Code Scanning default setup (CodeQL) via the repository API.
Do not invent custom query packs. Stop after two gate failures.

GATE: Code scanning shows as configured

## Phase 3

> unverified — check before pasting

### AGENT-WHAT-NOT: Add or improve a "What this is not" section
Clear non-goals prevent wrong expectations and support tickets.
In README.md, ensure a short "## What this is not" section with 3–5 concrete bullets.
Keep tone plain. Do not invent features.

GATE: grep -qi 'what this is not' README.md

## Phase final — verify & PR

1. Run project tests / verify script if present.
2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: SEC-CODEQL, AGENT-WHAT-NOT
3. Push branch `chore/argus-agent` (or continue the existing Argus branch).
4. Open a Pull Request whose body lists the fix IDs above.

GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED
```

### Auto-safe (controller may open PRs)

- `HYGIENE-GITATTRIBUTES` — Add language attribution (.gitattributes) — GATE: `test -f .gitattributes`
- `HYGIENE-TOPICS` — Set 3–5 specific repository topics — GATE: `true`
- `HYGIENE-SECURITY-MD` — Add SECURITY.md — GATE: `test -f SECURITY.md`
- `HYGIENE-CONTRIBUTING` — Add CONTRIBUTING.md — GATE: `test -f CONTRIBUTING.md`
- `HYGIENE-COC` — Add CODE_OF_CONDUCT.md — GATE: `test -f CODE_OF_CONDUCT.md`
- `HYGIENE-CI` — Add a basic CI workflow on the default branch — GATE: `test -d .github/workflows && ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null | head -1 | grep -q .`
- `HYGIENE-CODEOWNERS` — Add CODEOWNERS — GATE: `test -f CODEOWNERS -o -f .github/CODEOWNERS -o -f docs/CODEOWNERS`
- `HYGIENE-GITIGNORE` — Add a starter .gitignore — GATE: `test -f .gitignore`
- `SEC-CODEQL-WORKFLOW` — Add CodeQL workflow pack — GATE: `test -f .github/workflows/codeql.yml -o -f .github/workflows/codeql.yaml`
- `SEC-DEPENDABOT-ENABLE` — Enable Dependabot alerts via API — GATE: `true`
- `SEC-SECRET-SCAN-ENABLE` — Enable secret scanning + push protection via API — GATE: `true`
