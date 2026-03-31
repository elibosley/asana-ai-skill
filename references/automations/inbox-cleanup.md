# Inbox Cleanup Workflow Spec

## Purpose

Run `inbox-cleanup` as an AI-gated My Tasks triage workflow.

The workflow should not let Python decide the final buckets. Python should fetch the tasks, package the context, and apply a reviewed plan. The AI should:

- suggest the high-level categories for this specific inbox
- save those categories and task decisions to JSON
- bucket only the clear tasks automatically
- surface ambiguous tasks as explicit user questions
- suggest new categories or sections when the existing ones do not fit

## Core Principle

`inbox-cleanup` is now a two-phase workflow:

1. Snapshot: fetch My Tasks context and emit a planning JSON.
2. Plan: let the AI author categories plus per-task decisions.
3. Apply: move only the tasks approved in the plan.

The bucket decision is the AI step. Python is the fetch/apply layer.

## Use When

- The user says “clean up my inbox”, “triage My Tasks”, or “work through my open tasks”.
- The user wants AI to decide the categories, not just file tasks into hard-coded review columns.
- The user wants unclear items called out before mutation.
- The user wants a reusable JSON artifact that can be reviewed, edited, or rerun.

## Commands

Generate the snapshot and plan scaffold:

```bash
python3 scripts/asana_api.py inbox-cleanup
python3 scripts/asana_api.py inbox-cleanup --snapshot-file /tmp/asana-inbox-snapshot.json
python3 scripts/asana_api.py inbox-cleanup --snapshot-file /tmp/asana-inbox-snapshot.json --plan-template-file /tmp/asana-inbox-plan.json
python3 scripts/asana_api.py inbox-cleanup --all-open --max-tasks 50
```

Preview or apply an AI-authored plan:

```bash
python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json
python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json --apply
python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json --apply --include-low-confidence
```

## Inputs

Required placeholders:

- none when using the default authenticated user context

Optional placeholders:

- `SOURCE_SECTION`, default `Recently assigned`
- `ALL_OPEN`, when the user wants a wider sweep
- `MAX_TASKS`
- `SNAPSHOT_FILE`
- `PLAN_TEMPLATE_FILE`
- `PLAN_FILE`
- `INCLUDE_LOW_CONFIDENCE`

## Snapshot Contract

`inbox-cleanup` without `--plan-file` emits a snapshot payload with:

- `workflow: "asana_inbox_cleanup_snapshot"`
- `version`
- `generated_at`
- `my_tasks`
- `source_sections`
- `all_open`
- `current_section_counts`
- `existing_sections`
- `starter_category_seeds`
- `tasks`
- `legacy_review_hints`
- `instructions`
- `plan_template`

Each task in `tasks` includes hints that the AI can use while planning:

- `task_gid`
- `name`
- `permalink_url`
- `current_section`
- `project_state`
- `due_date`
- `reasons`
- `linked_prs`
- `task_read_hint`
- `classification_basis_hint`
- `suggested_next_action_hint`
- `ask_user_hint`
- `ai_help_summary_hint`
- `active_ai_action_hint`
- `legacy_category_hint`
- `legacy_target_section_hint`

The `legacy_*` fields are only hints. They are not the final answer.

## Plan Contract

The AI should author a JSON object with:

- `workflow: "asana_inbox_cleanup_plan"`
- `version`
- `generated_at`
- `my_tasks_gid`
- `source`
- `categories`
- `tasks`

### Categories

`categories` should reflect the actual inbox, not a fixed global taxonomy.

Each category should include:

- `slug`
- `name`
- `target_section_name`
- `description`

Suggested starting seeds:

- `execute_now`
- `needs_verification`
- `waiting_on_others`
- `likely_ready_to_close`
- `backlog_or_not_now`
- `needs_user_input`

The AI may replace, merge, or extend those seeds. If the inbox clearly needs a better fit, add a new category and section such as:

- `urgent-decisions`
- `needs-scoping`
- `release-watch`
- `customer-follow-up`

### Tasks

Each task entry should include:

- `task_gid`
- `name`
- `decision`
- `category_slug`
- `target_section_name`
- `confidence`
- `why`
- `question`
- `notes`

Allowed `decision` values:

- `bucket`
- `ask_user`
- `leave_as_is`

Recommended `confidence` values:

- `high`
- `medium`
- `low`

## Planning Rules

### 1. Suggest categories before bucketing

Do not start by assigning tasks to the default review sections.

First look across the task list and answer:

- what kinds of work are actually present
- which categories matter today
- which existing sections fit
- which tasks need a new section/category

### 2. Only auto-bucket high-confidence tasks

If the next move is clear, the AI should set:

- `decision: "bucket"`
- a concrete `category_slug`
- a concrete `target_section_name`

If the next move is not clear, use:

- `decision: "ask_user"`
- a specific `question`

### 3. Leave bad fits alone unless a better category exists

If a task does not fit any current category and the AI cannot confidently invent a better one, keep it interactive:

- `decision: "ask_user"`

If there is a clear pattern across several tasks, add a new category and use it.

### 4. Prefer real work reads over filing labels

For each task the AI should still determine:

- what this task really is
- why that category fits
- the next practical move
- what user input is still missing

### 5. Questions should unblock action

Good `question` examples:

- “Is this still waiting on legal, or should this move back into active drafting?”
- “Do you want this treated as release verification or as a reopen-and-fix task?”
- “Is this still priority this week, or should it be parked in backlog cleanup?”

Bad `question` examples:

- “What do you want to do?”
- “Please clarify.”

## Apply Rules

When `--plan-file` is passed without `--apply`, the helper previews what would happen.

When `--apply` is passed:

- move only tasks with `decision: "bucket"`
- create missing target sections when needed
- leave `ask_user` tasks untouched
- leave `leave_as_is` tasks untouched
- leave low-confidence bucket decisions untouched unless `--include-low-confidence` is set
- never complete tasks

## Example Plan

```json
{
  "workflow": "asana_inbox_cleanup_plan",
  "version": 1,
  "generated_at": "2026-03-31T13:45:00Z",
  "my_tasks_gid": "123",
  "source": {
    "workflow": "asana_inbox_cleanup_snapshot",
    "generated_at": "2026-03-31T13:40:00Z",
    "all_open": true
  },
  "categories": [
    {
      "slug": "release-watch",
      "name": "Release Watch",
      "target_section_name": "Release / Ship Watch",
      "description": "Tasks that need verification, rollout watching, or close-out after a PR already landed."
    },
    {
      "slug": "urgent-decisions",
      "name": "Urgent Decisions",
      "target_section_name": "Urgent Decisions",
      "description": "Decision-heavy tasks that block other work and need the user's call."
    }
  ],
  "tasks": [
    {
      "task_gid": "456",
      "name": "Verify PR #4242 in preview",
      "decision": "bucket",
      "category_slug": "release-watch",
      "target_section_name": "Release / Ship Watch",
      "confidence": "high",
      "why": "The task already references a shipped PR and the next move is verification, not new implementation.",
      "question": "",
      "notes": "Treat as verification queue."
    },
    {
      "task_gid": "789",
      "name": "Decide policy rollout communication",
      "decision": "ask_user",
      "category_slug": "urgent-decisions",
      "target_section_name": "",
      "confidence": "low",
      "why": "It is clearly a decision task, but the urgency and owner expectation are still ambiguous.",
      "question": "Do you want to handle this personally now, or should AI draft the recommendation first?",
      "notes": ""
    }
  ]
}
```

## Prompt Template

```text
Use the installed Asana skill.

Run `python3 scripts/asana_api.py inbox-cleanup --all-open --snapshot-file /tmp/asana-inbox-snapshot.json --plan-template-file /tmp/asana-inbox-plan.json`.

Read the snapshot JSON and decide what high-level categories this inbox actually needs.

Write an AI-authored plan JSON to `/tmp/asana-inbox-plan.json`:
- define categories first
- bucket only high-confidence tasks
- leave ambiguous tasks as `ask_user`
- suggest new categories or section names when the existing ones do not fit

Then preview the plan with:
`python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json`

Only apply it if the user confirms:
`python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json --apply`
```

## Invocation Short Forms

- `Use the Asana skill and run the AI-gated inbox cleanup spec.`
- `Generate an inbox snapshot, suggest categories, and write the cleanup plan JSON.`
- `Do not auto-sort my tasks. Propose the categories first, then bucket the clear ones.`
- `Run inbox-cleanup interactively and leave the unclear tasks as questions for me.`

## Scheduling Guidance

Good recurring uses:

- morning intake sweeps that stop at plan generation
- weekly all-open My Tasks reviews where the AI updates categories for the current backlog shape

Less suitable:

- fully unattended task moves without a reviewed plan
