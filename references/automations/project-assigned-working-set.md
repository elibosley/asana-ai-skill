# Project Assigned Working Set Workflow Spec

## Purpose

Turn `project-assigned-tasks` output into an implementation-ready working set instead of a raw checklist.

This is the long-form source of truth for the assigned-work triage workflow built around `project-assigned-tasks`.
Use it when the user wants to know what they should actually work on in a project.

## Use When

- The user asks what is assigned to them in a specific project.
- The user asks what they should work on now inside a project.
- The workflow should separate real implementation work from QA, repro, backlog, or cleanup items.

## Works With

- `python3 scripts/asana_api.py project-assigned-tasks <project_gid> --completed false`
- `python3 scripts/asana_api.py project-assigned-tasks <project_gid> --completed false --include-task-position --include-comments --comment-limit 3 --include-attachments`
- `python3 scripts/asana_api.py task-bundle <task_gid> --project-gid <project_gid>`
- `python3 scripts/asana_api.py task-status <task_gid>`

## Inputs

Required placeholders:

- `PROJECT_GID`

Optional placeholders:

- `ASSIGNEE_IDENTIFIER`, default current user when appropriate
- `COMMENT_LIMIT`, default helper behavior or `3`
- `MAX_DEEP_DIVE_TASKS`, the short list that should receive `task-bundle`

## Output Contract

The workflow should return a contextual working set, not a raw JSON dump.

Required buckets:

- `implemented / QA only`
- `active code-now`
- `needs repro before code`
- `backlog / workflow cleanup`

If publishing markdown or a user-facing summary:

- explicitly label the raw snapshot versus the interpreted working set

## Two-Pass Workflow

### Pass 1

Run `project-assigned-tasks` with context flags:

- `--include-task-position`
- `--include-comments`
- `--comment-limit 3`
- `--include-attachments`

Use this pass to evaluate:

- section order
- task position
- recent comments
- parent context
- attachments

### Pass 2

Run `task-bundle` only for the short list that still looks like `active code-now`.

Do not run deep bundle reads for the whole project assignment list unless the user explicitly wants exhaustive analysis.

## Classification Guidance

### implemented / QA only

Tasks that already look built, handed off, or mostly waiting on validation.

### active code-now

Tasks where the next meaningful step is implementation today.

### needs repro before code

Tasks where the evidence is weak, the bug needs reproduction, or more details are needed before implementation.

### backlog / workflow cleanup

Tasks that are assigned but should not drive immediate execution.

## Standard Output Shape

Recommended structure:

```text
# Project Working Set

Short paragraph on the real shape of the work.

## Active Code-Now
- [Task name](TASK_URL) — one-line reason

## Needs Repro Before Code
- [Task name](TASK_URL) — one-line reason

## Implemented / QA Only
- [Task name](TASK_URL) — one-line reason

## Backlog / Workflow Cleanup
- [Task name](TASK_URL) — one-line reason
```

## Prompt Template

```text
Use the installed Asana skill.

Build an implementation-ready working set for PROJECT_GID.

First run project-assigned-tasks with contextual flags so the result includes task position, recent comments, attachments, and parent context.

Split the work into:
- implemented / QA only
- active code-now
- needs repro before code
- backlog / workflow cleanup

Then run task-bundle only for the short list in active code-now.

Do not stop at the raw Asana snapshot.
Return the interpreted working set and clearly label the difference between the raw snapshot and the execution-oriented read.
```

## Invocation Short Forms

- `Use the Asana skill and run the full spec in references/automations/project-assigned-working-set.md.`
- `Build the project working set for this project.`
- `Use the assigned-work working-set spec and tell me what is actually code-now.`

## Scheduling Guidance

Usually manual.

Good recurring uses:

- start-of-day project focus checks
- pre-sprint planning
- weekly assignee cleanup

## Caveats

- Assigned does not always mean actionable.
- Subtasks without direct project membership still matter if parent context indicates project relevance.
- Recent comments can flip the real next action even when the section name looks straightforward.

## Validation Checklist

- Confirm the contextual `project-assigned-tasks` flags were used.
- Confirm the summary is not just a raw checklist.
- Confirm only the short list received `task-bundle`.
- Confirm the user-facing output separates raw snapshot from interpreted working set.

## Relationship To Cookbook

This file is the full spec.
The shorter discovery entry lives in `references/recipes.md`.
