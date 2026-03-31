---
name: asana-inbox-cleanup
description: Use when the user wants AI-gated My Tasks triage and section filing. Thin entrypoint to the installed asana skill's inbox cleanup workflow spec.
---

# Asana Inbox Cleanup

This is a thin workflow entrypoint for the installed `asana` skill.

## Workflow

1. Load the sibling base skill at `../asana/SKILL.md`.
2. Load the full workflow spec at `../asana/references/automations/inbox-cleanup.md`.
3. Follow that spec end to end with the installed helper commands from the base skill.
4. Treat snapshot, AI plan, and apply as distinct phases.
5. Only move tasks when the reviewed plan says to bucket them and the run is explicitly in apply mode.

## Guardrails

- Do not let Python choose the final categories or bucket decisions.
- Do not auto-bucket ambiguous tasks.
- Ask the user only for the items the plan marks as `ask_user`.
