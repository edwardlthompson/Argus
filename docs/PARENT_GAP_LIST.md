# Parent / child gap list

**Parent:** [edwardlthompson/agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap) (`v1.12.0`)  
**Child:** Argus (this repository)  
**Policy:** Argus is a **product child**, not a template fork. Inherit lineage + agent hygiene; do not vendor the full template runtime (`modules/`, `examples/`, full `scripts/agent-run.py` surface).

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
| G12 | Full template `scripts/agent-run.py` / lifecycle | Keep Argus `scripts/verify.*`; document as wont | ❌ |
| G13 | Full Cursor hooks/skills/plugin pack | Thin adapters only; upgrade via parent docs | ❌ |
| G14 | Template `modules/` / `examples/` / `TEMPLATE_INDEX` | N/A for product child | ❌ |
| G15 | CodeQL / secret-scan workflows | Rely on GitHub defaults + Dependabot; optional later | ❌ |

**Board rule:** New parent upgrades → open a BUILD_PLAN row, re-diff this table, close or wont each gap.
