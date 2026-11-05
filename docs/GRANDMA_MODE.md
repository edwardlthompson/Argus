# Grandma Mode

When Argus needs a human, instructions must be usable by a non-technical person.

## Principles

1. Prefer GitHub UI clicks over terminal commands.
2. One sentence “why” before the steps.
3. Numbered steps; one action per step.
4. End with **Done when …** — a visible success condition.
5. No jargon (say “click Settings”, not “mutate repository metadata”).
6. If a shell command is unavoidable, it must be a single safe command with no flags that destroy data.

## Notification copy

Keep it short: “Argus needs you for 2 small tasks” + a link to the HTML report.

## Authors of human fixes

When adding a `class: human` entry to `config/fixes.yaml`, write `human_steps` as if explaining to a careful grandparent who can use a browser but does not know git.
