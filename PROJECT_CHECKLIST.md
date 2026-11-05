# Project Checklist

> Argus · Stack: `python` · License: `MIT` · Parent: `edwardlthompson/agent-project-bootstrap@1.12.0`  
> Status: 🔲 open · ✅ done · ❌ blocked / wont

## Setup

- ✅ README updated with value proposition and quickstart
- ✅ Environment variables configured (`.env.example`; `.env` not committed)
- ✅ `docs/spec.md` and `docs/plan.md` filled for the first milestone
- ✅ Initial tests passing locally (`pytest`)
- ❌ Pre-commit hooks from full template — wont (lean child; use `scripts/verify.*`)

## Security & CI

- ✅ CI workflow present (`.github/workflows/ci.yml`)
- ❌ CodeQL workflow vendor — wont for now (enable on GitHub when published)
- ✅ Dependabot config present
- 🔲 Branch protection on default branch — optional follow-up
- ✅ `SECURITY.md` present

## Agent adapters / lineage

- ✅ `AGENT.md` holds the product brief
- ✅ `AGENTS.md` reviewed for Argus
- ✅ Thin adapters present (Cursor / Claude / Cline / Copilot / Gemini)
- ✅ `.template-version` + `.template-update.json` + `docs/PARENT_GAP_LIST.md`

## Next

1. `argus doctor`
2. `argus run --dry-run`
3. Publish remote + enable Pages / branch protection `[HUMAN]`
