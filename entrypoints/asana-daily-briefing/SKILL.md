---
name: asana-daily-briefing
description: Use when the user wants a morning command center for My Tasks. Thin entrypoint to the installed asana skill's daily briefing workflow spec.
---

# Asana Daily Briefing

This is a thin workflow entrypoint for the installed `asana` skill.

## Workflow

1. Load the sibling base skill at `../asana/SKILL.md`.
2. Load the full workflow spec at `../asana/references/automations/daily-briefing.md`.
3. Follow that spec end to end with the installed helper commands from the base skill.
4. Keep the workflow read-only unless the user explicitly asks for something else.
5. Return the final AI-authored briefing, not the intermediate plan JSON, unless the user asks to inspect the plan or snapshot.

## Guardrails

- Do not fall back to a raw task dump.
- Do not let Python own the presentation template.
- The final user-facing briefing should come from the AI-authored `final_markdown` field defined by the workflow spec.
