# Parent / child gap list

**Parent:** [edwardlthompson/agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap) (`v1.13.0`)  
**Child:** Argus (this repository)  
**Policy:** Argus is a **product child**, not a template fork. Inherit lineage + Cursor FOSS surface; do not vendor full template lifecycle (`modules/`, `examples/`, full `scripts/lib`).

Status: ✅ closed · ❌ wont (documented) · 🔲 open

| ID | Gap | Resolution | Status |
|----|-----|------------|--------|
| G01 | No declared parent / `.template-version` | Pin `1.12.0`; add `.template-update.json` | ✅ |
| G02 | Missing `bootstrap.config.json` | Python FOSS manifest for Argus | ✅ |
| G03 | Missing child `AGENTS.md` product card | Argus router; stack `python` | ✅ |
| G04 | No Cursor/Claude/Cline adapters | Thin `main.mdc`, `CLAUDE.md`, `.clinerules`, `GEMINI.md` | ✅ |
| G05 | Missing `SECURITY.md` / `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` | Community files for this repo | ✅ |
| G06 | Agent memory at wrong path | `.agent/AGENT_MEMORY.md` + `DECISION_LOG.md` | ✅ |
| G07 | Missing `docs/spec.md` / `docs/plan.md` | Product spec + plan stubs | ✅ |
| G08 | No `PROJECT_CHECKLIST.md` | Child checklist (lean) | ✅ |
| G09 | No Dependabot | `.github/dependabot.yml` for pip + Actions | ✅ |
| G10 | No `.gitattributes` | LF + linguist hints for Python | ✅ |
| G11 | README silent on parent | Lineage section + upgrade pointer | ✅ |
| G12 | Full template `scripts/lib` / lifecycle | Thin `scripts/agent-run.py` shim only; `verify.*` remains source of truth | ❌ |
| G13 | Cursor FOSS pack (commands/hooks/skills/agents/plugin) | Commands + hooks + curated skills/agents + `argus-foss` plugin; Android/Sprint0 skills omitted | ✅ |
| G14 | Template `modules/` / `examples/` / `TEMPLATE_INDEX` | N/A for product child | ❌ |
| G15 | CodeQL / secret-scan workflows | Rely on GitHub defaults + Dependabot; optional later | ❌ |

**G13 note:** Omitted by design: `emulator`, `espresso-android16`, `blender-icons`, `sprint0-signoff`, full canvas-bootstrap-status. Upgrade: re-copy `.cursor/commands|hooks|skills`, re-stamp Argus banners/prefaces, extend shim verb sets from exit-2 unknowns.

**Board rule:** New parent upgrades → open a BUILD_PLAN row, re-diff this table, close or wont each gap.
