# Argus hygiene constitution (human-readable)

This mirrors `config/fixes.yaml`. Prefer editing the YAML — it is what the loader enforces.

1. Attribute language correctly (`.gitattributes`).
2. Keep repository description ≤ 120 characters.
3. Use 3–5 specific topics (strip generic tags).
4. Ship a LICENSE that matches GitHub metadata.
5. Provide SECURITY.md, CONTRIBUTING.md, and CODE_OF_CONDUCT.md.
6. Enable Dependabot alerts / security updates (human Settings when required).
7. Prefer semver tags; avoid noisy non-semver tag sprawl.
8. Enable secret scanning where available.
9. Keep CI on the default branch.
10. Parked/archived repos get hygiene + security only — no feature agent work.
