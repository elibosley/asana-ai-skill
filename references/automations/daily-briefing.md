# Daily Briefing Workflow Spec

## Purpose

Run `daily-briefing` as an AI-gated, read-only morning planning workflow.

The command should not use built-in heuristics to decide what is actionable. Python should fetch the current My Tasks context and render an AI-authored plan. The AI should:

- scan the user's open tasks
- decide which tasks are actually worth attention today
- group them into the right morning buckets
- explain why each highlighted task matters
- leave ambiguous items as explicit user questions

## Core Principle

`daily-briefing` is now a two-phase read-only workflow:

1. Snapshot: fetch open My Tasks context and emit a planning JSON.
2. Plan: let the AI choose the meaningful buckets and highlighted tasks.
3. Render: turn that reviewed plan into JSON or markdown.

The actionability decision belongs to the AI plan, not to Python heuristics.
For normal agent use, the user should not be asked to author the plan manually. The plan JSON is an internal artifact the agent creates automatically before showing the final briefing.

## Use When

- The user asks, `what should I focus on this morning?`
- The user wants a command center instead of a filing pass.
- The user wants AI to decide what is actionable rather than relying on fixed rules.
- The workflow should stay read-only while still being opinionated.

## Commands

Generate the daily briefing snapshot and plan scaffold:

```bash
python3 scripts/asana_api.py daily-briefing
python3 scripts/asana_api.py daily-briefing --snapshot-file /tmp/asana-daily-briefing-snapshot.json
python3 scripts/asana_api.py daily-briefing --snapshot-file /tmp/asana-daily-briefing-snapshot.json --plan-template-file /tmp/asana-daily-briefing-plan.json
python3 scripts/asana_api.py daily-briefing --max-tasks 50
```

Render an AI-authored plan:

```bash
python3 scripts/asana_api.py daily-briefing --plan-file /tmp/asana-daily-briefing-plan.json
python3 scripts/asana_api.py daily-briefing --plan-file /tmp/asana-daily-briefing-plan.json --markdown
```

## Inputs

Required placeholders:

- none when using the default authenticated user context

Optional placeholders:

- `MAX_TASKS`
- `SNAPSHOT_FILE`
- `PLAN_TEMPLATE_FILE`
- `PLAN_FILE`

## User Experience

The default expected behavior is:

1. the agent runs `daily-briefing`
2. the agent writes the plan JSON itself
3. the agent renders the final morning command center
4. the agent only asks the user about tasks marked `ask_user`

The plan file exists so the workflow stays auditable and inspectable. It is not meant to make the user do extra work during a normal morning briefing run.

## Snapshot Contract

`daily-briefing` without `--plan-file` emits a snapshot payload with:

- `workflow: "asana_daily_briefing_snapshot"`
- `version`
- `generated_at`
- `my_tasks`
- `open_task_count`
- `tasks_considered`
- `current_section_counts`
- `starter_buckets`
- `tasks`
- `instructions`
- `plan_template`

Each task includes raw context for the AI to reason over:

- `task_gid`
- `name`
- `url`
- `current_section`
- `due_date`
- `completed`
- `project_memberships`
- `project_names`
- `linked_prs`
- `primary_pr`
- `notes_excerpt`
- `recent_comment_excerpts`
- `follower_count`
- `collaborator_count`
- `raw_signals`

This snapshot should help the AI decide what deserves attention today without pre-bucketing the tasks.

## Plan Contract

The AI should author a JSON object with:

- `workflow: "asana_daily_briefing_plan"`
- `version`
- `generated_at`
- `my_tasks_gid`
- `source`
- `overview`
- `focus`
- `categories`
- `tasks`

### Categories

`categories` define the visible sections of the morning briefing.

Default seeds are:

1. `Execute Now`
2. `Release / Ship Watch`
3. `Needs Verification`
4. `Needs Follow-Up`
5. `Likely Ready To Close`
6. `Background / Not Today`

The AI can keep these stable or introduce a better fit if the inbox shape clearly demands it.

Each category should include:

- `slug`
- `name`
- `description`
- `display_order`

### Tasks

Each task entry should include:

- `task_gid`
- `name`
- `decision`
- `bucket_slug`
- `confidence`
- `why`
- `next_action`
- `question`
- `notes`

Allowed `decision` values:

- `highlight`
- `ask_user`
- `omit`

Recommended `confidence` values:

- `high`
- `medium`
- `low`

## Planning Rules

### 1. Decide what is actionable, not just what exists

The AI should highlight only the tasks that deserve space in a morning command center.

Do not dump the full open-task list into the output.

### 2. Keep it read-only but opinionated

The output should still answer:

- what matters today
- why it matters
- what the likely next move is

But the workflow must not mutate tasks, move sections, or post comments.

### 3. Use `ask_user` for ambiguity

If a task might matter today but the missing assumption is important, do not force it into a bucket.

Use:

- `decision: "ask_user"`
- one concrete `question`

### 4. Omit low-signal noise

If a task is clearly not part of today's command center, use:

- `decision: "omit"`

### 5. Prefer reasons tied to today's work

Good `why` examples:

- “This has a concrete preview validation step and should be cleared before new implementation.”
- “This blocks another thread and needs one follow-up before it can move.”
- “This looks effectively done and only needs a final close-out pass.”

Bad `why` examples:

- “This is a task.”
- “It seems important.”

## Output Contract

Rendering the plan should produce:

- a short morning overview
- a short focus line
- bucketed highlighted tasks with direct links
- a `Needs Your Input` section when the AI marked tasks as `ask_user`

Markdown is the preferred human-facing mode.

## Example Plan

```json
{
  "workflow": "asana_daily_briefing_plan",
  "version": 1,
  "generated_at": "2026-03-31T14:00:00Z",
  "my_tasks_gid": "123",
  "source": {
    "workflow": "asana_daily_briefing_snapshot",
    "generated_at": "2026-03-31T13:55:00Z"
  },
  "overview": "Three tasks deserve attention this morning.",
  "focus": "Finish verification and unblock follow-ups before pulling in fresh implementation work.",
  "categories": [
    {
      "slug": "execute-now",
      "name": "Execute Now",
      "description": "Tasks worth active work immediately.",
      "display_order": 1
    },
    {
      "slug": "needs-follow-up",
      "name": "Needs Follow-Up",
      "description": "Tasks that need one concrete response or unblock.",
      "display_order": 2
    }
  ],
  "tasks": [
    {
      "task_gid": "456",
      "name": "Verify PR #4242 in preview",
      "decision": "highlight",
      "bucket_slug": "execute-now",
      "confidence": "high",
      "why": "This has a concrete verification step and should be cleared before new implementation starts.",
      "next_action": "Run the preview verification pass now.",
      "question": "",
      "notes": ""
    },
    {
      "task_gid": "789",
      "name": "Decide policy rollout communication",
      "decision": "ask_user",
      "bucket_slug": "",
      "confidence": "low",
      "why": "It may be important today, but the urgency versus delegation choice is unclear.",
      "next_action": "",
      "question": "Do you want this treated as a top-of-day decision or as a draft-for-review item?",
      "notes": ""
    }
  ]
}
```

## Prompt Template

```text
Use the installed Asana skill.

Run `python3 scripts/asana_api.py daily-briefing --snapshot-file /tmp/asana-daily-briefing-snapshot.json --plan-template-file /tmp/asana-daily-briefing-plan.json`.

Read the snapshot JSON and decide which tasks actually belong in today's morning command center.

Write an AI-authored plan JSON to `/tmp/asana-daily-briefing-plan.json`:
- highlight only the tasks worth attention today
- keep the buckets useful and easy to scan
- leave ambiguous tasks as `ask_user`
- omit low-signal tasks from the visible briefing

Then render the reviewed plan with:
`python3 scripts/asana_api.py daily-briefing --plan-file /tmp/asana-daily-briefing-plan.json --markdown`

Do not mutate tasks, move sections, or add comments.

Do this end to end yourself. Do not stop after generating the snapshot or ask the user to fill in the plan unless the user explicitly wants to inspect the intermediate JSON.
```

## Invocation Short Forms

- `Use the Asana skill and run the AI-gated daily briefing spec.`
- `Generate the daily briefing snapshot, decide what is actionable, and render the plan in markdown.`
- `Do not use built-in task heuristics; let AI decide today's actionable list.`
- `Run daily-briefing as a read-only AI morning command center.`

## Scheduling Guidance

Good recurring uses:

- weekday mornings
- one run early enough to shape the workday

Best practice:

- schedule snapshot generation or full AI rendering, but keep it read-only
