# Threat model — Argus dual plane

## Assets

- Portfolio repository contents and settings
- Operator PAT / fine-grained token
- Security findings (Dependabot/CodeQL gaps, vulns)
- Grandma Issue bodies (enablement steps)

## Trust boundaries

| Zone | Trust |
|------|-------|
| Public product `Argus` | World-readable; no live findings; CI fixtures/tests |
| Private `argus-runner` | Owner ACL; full artifacts + Issues + secrets |
| Public `USER/USER` profile | Marketing Overview only — no security gaps |
| Chat webhooks | Treat as private; send counts + links only |

## Token blast radius

`ARGUS_GITHUB_TOKEN` on the runner can open PRs and Issues across allowed repos. Mitigations:

- Store secret only on the **private** runner
- Prefer fine-grained PAT limited to owned repos
- `config/allowlist.yaml` `owner_only` default
- `max_auto_prs_per_run` in `safety.yaml`
- Dry-run before first apply ([WEEKLY_APPLY.md](WEEKLY_APPLY.md))

## Attacker goals (and controls)

| Goal | Control |
|------|---------|
| Read your missing security controls | Never publish on public Pages/Issues; `security_issues` only if controller private; doctor guard |
| Abuse PAT | Private runner secrets; least privilege; never commit `.env` |
| Tamper public product into applying | Product CI must not run apply with owner PAT against portfolio |
| Poison profile README | Compose from API + YAML only; no LLM; PR review before merge |

## Residual risk

GitHub Actions logs on the private runner are visible to anyone with repo access — keep the runner private and membership tight.
