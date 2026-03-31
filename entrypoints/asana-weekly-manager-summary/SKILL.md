---
name: asana-weekly-manager-summary
description: Use when the user wants a manager-facing weekly summary of another person's Asana work. Thin entrypoint to the installed asana skill's weekly manager summary workflow spec.
---

# Asana Weekly Manager Summary

This is a thin workflow entrypoint for the installed `asana` skill.

## Workflow

1. Load the sibling base skill at `../asana/SKILL.md`.
2. Load the full workflow spec at `../asana/references/automations/weekly-manager-summary.md`.
3. Follow that spec end to end with the installed helper commands from the base skill.
4. Produce one concise manager-facing artifact with direct task links and short follow-up prompts where useful.

## Guardrails

- Do not stop at raw search results.
- Keep the result operational and scannable.
- Include direct Asana links for each referenced task.
