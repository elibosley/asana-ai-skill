# Weekly Manager Summary Automation Spec

## Purpose

Generate a concise manager-facing weekly summary for one employee's assigned Asana work, then create a single follow-up task or note for the manager.

This is the long-form source of truth for the weekly employee-to-manager summary workflow.
Use it when the agent should execute, edit, review, or schedule this automation.

## Use When

- The user wants a weekly summary of another employee's assigned work.
- The user wants a recurring manager report instead of a raw Asana search result.
- The automation should create one manager-facing task or note that is easy to scan.
- The user wants draft follow-up prompts for items that are active, stalled, blocked, or waiting on manager input.

## Works With

- `python3 scripts/asana_api.py search-tasks`
- `python3 scripts/asana_api.py task`
- `python3 scripts/asana_api.py task-comments`
- `python3 scripts/asana_api.py task-stories`
- `python3 scripts/asana_api.py create-task`
- `python3 scripts/asana_api.py update-task`
- `python3 scripts/asana_api.py users`
- `python3 scripts/asana_api.py show-cache`

## Inputs

Required placeholders:

- `EMPLOYEE_NAME`
- `EMPLOYEE_GID`
- `WORKSPACE_GID`
- `MANAGER_IDENTIFIER`

Optional placeholders:

- `PROJECT_GID` or a small set of project gids when the summary should be scoped
- `LOOKBACK_DAYS` for "completed this week" logic, default `7`
- `ACTIVE_WINDOW_DAYS` for recently updated logic, default `7`
- `TASK_TITLE`, default `Weekly Review: EMPLOYEE_NAME's Asana Summary`
- `DUE_DATE_RULE`, usually "today" on the run date

## Output Contract

The automation must produce one manager-facing artifact.

Default artifact:

- One Asana task assigned to `MANAGER_IDENTIFIER`
- Due on the run date
- Title: `Weekly Review: EMPLOYEE_NAME's Asana Summary`
- Notes containing:
  - `Completed`
  - `In Progress`
  - `Blocked / Stalled`
  - any recommended follow-up messages

For every referenced task, include:

- the task name
- a direct Asana link
- assignee
- due date if present
- short contextual reason for the bucket

## Required Buckets

### Completed

Tasks marked complete within the last `LOOKBACK_DAYS`.

### In Progress

Open tasks that are either:

- due within the next `LOOKBACK_DAYS`, or
- recently updated within the last `ACTIVE_WINDOW_DAYS`

### Blocked / Stalled

Open tasks that appear inactive or at risk, such as:

- overdue tasks
- tasks with no recent activity
- tasks that appear to be waiting for review, feedback, approval, or input

## Deterministic Rules

Use deterministic rules first.

Classify into `Completed`, `In Progress`, and `Blocked / Stalled` using:

- `completed`
- `completed_at`
- `due_on` / `due_at`
- `modified_at`
- recent stories/comments

Recent activity defaults:

- "recently updated" means activity in the last `ACTIVE_WINDOW_DAYS`
- "completed this week" means `completed_at` in the last `LOOKBACK_DAYS`

## Follow-Up Message Rules

For each `In Progress` or `Blocked / Stalled` task, prepare a short suggested message the manager could send to the employee.

Examples:

- `What's the current status here, and do you need anything from me to unblock it?`
- `Can you confirm whether this is still on track for the due date?`
- `This looks stalled. What is the blocker and what is the next concrete step?`
- `Are you waiting on a decision or approval from me here?`

The summary artifact should include these suggestions only when they add value.

## Prompt Template

```text
Use the installed Asana skill.

Search Asana for all tasks assigned to EMPLOYEE_NAME (GID EMPLOYEE_GID) in workspace GID WORKSPACE_GID.

If a project scope is provided, limit the scan to that project or project set. Otherwise, search the whole workspace.

Review the matching tasks and categorize them into three groups:

1. Completed this week: tasks marked complete in the last 7 days
2. In Progress: tasks that are open and due in the next 7 days or recently updated
3. Blocked / Stalled: tasks that are open and overdue or show no recent activity

Write a concise manager-facing summary with three clearly labeled sections:
- Completed
- In Progress
- Blocked / Stalled

For every task mentioned:
- include the task name
- include a direct Asana link using:
  (https://app.asana.com/0/WORKSPACE_GID/TASK_GID)
- include the due date if present
- include a short explanation of why it belongs in that section

Then create a single Asana task assigned to MANAGER_IDENTIFIER in workspace GID WORKSPACE_GID.

Set:
- title: Weekly Review: EMPLOYEE_NAME's Asana Summary
- due date: today's date

Put the full summary in the task notes.

Create the task directly without preview.

Also prepare recommended follow-up messages for each task that is in progress, blocked, stalled, or appears to be waiting on a response from the manager.

Return the final task link.
```

## Scheduling Guidance

Good default schedule:

- weekly
- same weekday and time each week
- manager's local timezone

Typical cadence:

- Friday morning

## Implementation Notes

- Prefer `search-tasks` plus follow-up task detail reads over board-only scans.
- Use direct task reads only for the small set that actually make the final summary.
- Keep the output concise enough that a manager can scan it in one pass.
- If the manager already provided an existing weekly review task for that date and asked for an update, update it instead of creating a duplicate.

## Caveats

- Workspace-wide searches can be noisy; use project scoping when the user asks for it.
- Completed tasks may still need manager visibility if they closed only very recently.
- Some tasks may look stale because comments happened outside the scanned window; do not overstate certainty.
- If the bucket is ambiguous, call that out instead of over-classifying.

## Validation Checklist

- Confirm the employee identity resolves correctly.
- Confirm the workspace or project scope is correct.
- Confirm the three required sections are present.
- Confirm every mentioned task includes a direct Asana link.
- Confirm the manager-facing task is assigned correctly.
- Confirm the due date matches the run date.
- Confirm follow-up message suggestions are included where helpful.

## Example Placeholder Set

- `EMPLOYEE_NAME`: `Employee Name`
- `EMPLOYEE_GID`: `EMPLOYEE_GID`
- `WORKSPACE_GID`: `WORKSPACE_GID`
- `MANAGER_IDENTIFIER`: `manager@example.com`

## Relationship To Cookbook

This file is the full spec.
The shorter discovery entry lives in `references/recipes.md`.
