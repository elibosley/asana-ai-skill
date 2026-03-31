# Close Out Sections Workflow Spec

## Purpose

Relocate tasks out of stale sections, then delete those sections only after they are actually empty.

This is the long-form source of truth for `close-out-sections`.
Use it when the agent should execute, edit, review, or schedule this workflow.

## Use When

- The user wants to retire old personal sections.
- The user wants to move everything out of one or more stale sections and then remove them.
- The workflow must stay preview-first and safety-oriented.

## Works With

- `python3 scripts/asana_api.py close-out-sections`
- `python3 scripts/asana_api.py close-out-sections --apply`
- `python3 scripts/asana_api.py sections <project_gid>`
- `python3 scripts/asana_api.py section-tasks <section_gid>`

## Inputs

Required placeholders:

- `PROJECT_GID`
- one or more `SECTION` identifiers
- `MOVE_TO` destination section

Optional placeholders:

- `COMPLETED_MODE`, one of:
  - completed
  - incomplete
  - all
- `APPLY`, preview by default

## Output Contract

The workflow should:

1. resolve source and destination sections
2. preview the exact moves by default
3. move only the requested task set
4. perform a final emptiness check
5. delete the source section only when safe

The user-facing output should include:

- exact source sections
- destination section
- how many tasks will move or did move
- whether deletion occurred
- any non-removable special-case outcome

## Default Safety Model

Preview-first by default.

Do not delete a section unless:

- the user requested apply mode
- the section is confirmed empty after the moves

## Completed Mode Semantics

### completed

Move only completed tasks.

### incomplete

Move only open tasks.

### all

Move everything.

## My Tasks Special Case

Treat `Recently assigned` as special.

It can often be emptied successfully, but Asana may still refuse to remove the column afterward.
In that case:

- report it as emptied but not removable
- stop instead of hammering the delete endpoint

## Standard Output Shape

Recommended structure:

```text
# Close Out Sections

Short paragraph on what will happen or what happened.

## Source Sections
- SECTION_NAME

## Destination
- DESTINATION_NAME

## Task Moves
- moved: COUNT
- skipped: COUNT

## Section Deletion
- deleted: yes/no
- note: any special-case behavior
```

## Prompt Template

```text
Use the installed Asana skill.

Run the close-out-sections workflow for PROJECT_GID.

Use these source sections:
- SOURCE_SECTION_LIST

Move tasks to:
- DESTINATION_SECTION

Use completed mode:
- COMPLETED_MODE

Preview by default unless I explicitly ask for apply mode.

Only delete a source section after the final emptiness check confirms it is safe.

If a My Tasks section like Recently assigned is emptied but not removable, report that outcome and stop instead of retrying.
```

## Invocation Short Forms

- `Use the Asana skill and run the full spec in references/automations/close-out-sections.md.`
- `Preview closing out these sections for me.`
- `Use the close-out-sections spec and move completed tasks out, then delete the empty sections if safe.`

## Scheduling Guidance

Usually manual.

Good recurring uses:

- end-of-week cleanup
- end-of-sprint section retirement

Avoid unattended scheduled apply mode unless the section names and completed-mode rules are tightly controlled.

## Caveats

- Section names can be reused; always resolve the exact project context first.
- Preview output is part of the contract; do not skip straight to mutation.
- Deletion depends on the final emptiness check, not the initial estimate.

## Validation Checklist

- Confirm source sections resolved correctly.
- Confirm destination section resolved correctly.
- Confirm preview mode ran unless apply was explicitly requested.
- Confirm only the requested task subset moved.
- Confirm deletion only happened after a final emptiness check.
- Confirm My Tasks edge cases were reported correctly.

## Relationship To Cookbook

This file is the full spec.
The shorter discovery entry lives in `references/recipes.md`.
