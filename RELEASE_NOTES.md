# Release notes — Argus 0.2.0

## Highlights

- **Private control plane** — Status-only public Pages; full reports as Actions artifacts; GitHub Issues inbox (`argus-inbox`); safe chat digests; `scan.yml`.
- **Cursor FOSS parity** — Slash commands, hooks, curated skills/subagents, `argus-foss` plugin, thin `scripts/agent-run.py` shim.

## Upgrade notes

- Prefer `python scripts/agent-run.py verify` for gates.
- Keep `config/inbox.yaml` → `security_issues: false` while the controller repo is public.
- Optional: make `edwardlthompson/Argus` private for strongest Issues ACL.

See `CHANGELOG.md` for the full list.
