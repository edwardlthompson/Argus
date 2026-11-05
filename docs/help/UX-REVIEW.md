# UX review (any IDE)

Ask your agent to score **shipped** UI against [`docs/ux-ui-guidelines.md`](../ux-ui-guidelines.md). In Cursor you can type `/ux-review` instead.

This is the same law used while building, not a second checklist. Do not invent screens. Do not implement unless you also ask for `/ux-apply`.

## Paste prompt

```
Read docs/help/UX-REVIEW.md and score the real UI. Write every change to the BUILD_PLAN UX inventory. Do not implement.

```

## Recipe

1. Read `docs/ux-ui-guidelines.md` and `.cursor/rules/ux-ui.mdc`. Tokens: `docs/DESIGN_GUIDE.md`.
2. Inspect real UI (template: `examples/web` + `examples/android` if present; child: `AGENT.md` + active stack). No UI stack → 0 items.
3. Walk first-time and returning flows. `--quick` skips live compare. `--compare` / `--a11y` / a named flow still record everything found.
4. Every change item (including removals and WCAG 2.2 AA / AAA) goes to `<!-- ux-inventory -->` in the same turn. Status `planned` / `in_progress` / `done` only.
5. `/build` does not drain inventory. Promote with `/ux-apply UX-NNN`.

See [`AGENT_PORTABILITY.md`](../AGENT_PORTABILITY.md) if your tool has no slash commands.
