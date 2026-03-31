---
name: asana-project-working-set
description: Use when the user wants an implementation-ready working set for assigned project tasks. Thin entrypoint to the installed asana skill's project-assigned working-set workflow spec.
---

# Asana Project Working Set

This is a thin workflow entrypoint for the installed `asana` skill.

## Workflow

1. Load the sibling base skill at `../asana/SKILL.md`.
2. Load the full workflow spec at `../asana/references/automations/project-assigned-working-set.md`.
3. Follow that spec end to end with the installed helper commands from the base skill.
4. Use the two-pass pattern from the spec.
5. Return an interpreted working set, not just the raw assigned-task payload.

## Guardrails

- Use `project-assigned-tasks` with context flags first.
- Use `task-bundle` only for the short list that still looks like real code-now work.
