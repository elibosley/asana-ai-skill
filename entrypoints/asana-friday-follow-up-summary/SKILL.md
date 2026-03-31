---
name: asana-friday-follow-up-summary
description: Use when the user wants a weekly summary of tasks they are involved in but do not own. Thin entrypoint to the installed asana skill's Friday follow-up summary workflow spec.
---

# Asana Friday Follow-Up Summary

This is a thin workflow entrypoint for the installed `asana` skill.

## Workflow

1. Load the sibling base skill at `../asana/SKILL.md`.
2. Load the full workflow spec at `../asana/references/automations/friday-follow-up-summary.md`.
3. Follow that spec end to end with the installed helper commands from the base skill.
4. Create or update one summary task for the target user instead of scattering the result across many notifications.

## Guardrails

- Use deterministic involvement and classification rules first.
- Only use LLM judgment when recent comments are ambiguous.
- Keep the final output auditable and link-rich.
