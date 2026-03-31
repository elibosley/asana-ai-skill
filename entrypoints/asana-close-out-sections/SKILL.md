---
name: asana-close-out-sections
description: Use when the user wants to retire stale My Tasks or project sections safely. Thin entrypoint to the installed asana skill's close-out-sections workflow spec.
---

# Asana Close Out Sections

This is a thin workflow entrypoint for the installed `asana` skill.

## Workflow

1. Load the sibling base skill at `../asana/SKILL.md`.
2. Load the full workflow spec at `../asana/references/automations/close-out-sections.md`.
3. Follow that spec end to end with the installed helper commands from the base skill.
4. Preview by default.
5. Delete a source section only after the final emptiness check confirms it is safe.

## Guardrails

- Do not skip the preview phase unless the user explicitly asks for apply mode.
- Treat `Recently assigned` as a special My Tasks case if Asana refuses deletion after the section is emptied.
