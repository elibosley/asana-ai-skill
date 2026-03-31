# Friday Follow-Up Summary Automation Spec

## Purpose

Create or update one weekly My Tasks summary covering open Asana tasks that are assigned to other people but may still need something from the target user.

This is the long-form source of truth for the recurring "involved but not owner" follow-up scan.
Use it when the agent should execute, edit, review, or schedule this automation.

## Use When

- The user says they lose track of tasks they are part of but do not own.
- The user wants one weekly follow-up task in My Tasks instead of many notifications.
- The user wants a recurring Friday check for tasks that may require their input.
- The automation should classify each task into `Needs my action` or `FYI / watching`.

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

- `TARGET_USER_IDENTIFIER`
- `WORKSPACE_GID`

Optional placeholders:

- `TARGET_USER_GID` when the identifier is not enough
- `TASK_TITLE`, default `Friday Follow-Up Summary`
- `LOOKBACK_DAYS`, default `7`
- `COMMENT_LOOKBACK_DAYS`, default `14`
- `PROJECT_GIDS` when the scan should be limited
- `RUN_TIMEZONE`, default to the user's timezone

## Scheduling

Recommended default:

- every Friday
- `7:30 AM`
- user's local timezone

Example human schedule:

- Friday morning at 7:30 AM in `America/Los_Angeles`

## Objective

Create or update one Asana task assigned to the target user so it appears in My Tasks.

Default task settings:

- title: `Friday Follow-Up Summary`
- assignee: target user
- due date: that same Friday

The task notes should summarize open tasks where:

- the target user is involved
- the task is assigned to someone else
- the target user may or may not owe action

## Involvement Rules

Only include incomplete tasks assigned to someone other than the target user.

Treat the target user as involved if any of the following are true:

- the target user is a collaborator
- the target user was mentioned in a recent comment or story
- there is an incomplete subtask assigned to the target user
- a custom field references the target user by name

## Classification Rules

Classify each included task into one of two buckets.

### Needs my action

Mark as `Needs my action` if any deterministic rule clearly applies:

- there is an incomplete subtask assigned to the target user
- a recent comment explicitly mentions the target user
- a recent comment asks the target user for:
  - input
  - review
  - approval
  - decision
  - answer
  - next step
- the latest unresolved request directed at the target user happened after the target user's last reply

### FYI / watching

Use `FYI / watching` when:

- the target user is involved, but
- there is no clear action needed right now

## LLM Fallback Rule

Use deterministic rules first.

Only use an LLM if the recent comments are ambiguous.

If an LLM is used, constrain it to structured JSON:

```json
{
  "needs_my_action": true,
  "confidence": 0.0,
  "reason": "short explanation"
}
```

Requirements:

- no free-form prose outside the JSON
- confidence should reflect ambiguity
- reason should stay short and auditable

## Duplicate Prevention

Before creating a new task, check whether a task already exists for the target user with:

- the exact title `Friday Follow-Up Summary`
- the same due date as the current run

If it exists:

- update it instead of creating a duplicate

## Output Contract

Create or update one summary task assigned to the target user with:

- title: `Friday Follow-Up Summary`
- assignee: target user
- due date: that same Friday
- notes/description containing the final summary

Required description format:

```text
Friday summary of open tasks I’m involved in that are assigned to someone else.

Needs my action
- (TASK_URL) — Assignee: ASSIGNEE_NAME — Due: DUE_DATE_OR_NONE
Reason: SHORT_REASON

FYI / watching
- (TASK_URL) — Assignee: ASSIGNEE_NAME — Due: DUE_DATE_OR_NONE
Reason: SHORT_REASON
```

If there are no matching tasks, still create or update the summary task and write:

```text
No open tasks assigned to others currently appear to need my attention.
```

Use direct Asana task links in this format:

```text
(https://app.asana.com/0/WORKSPACE_GID/TASK_GID)
```

## Prompt Template

```text
Use the installed Asana skill.

Every Friday morning, create or update one Asana task assigned to TARGET_USER_IDENTIFIER in workspace GID WORKSPACE_GID.

The task title should be:
"Friday Follow-Up Summary"

The task due date should be that same Friday.

Before creating a new task, check whether a task with that exact title and due date already exists for TARGET_USER_IDENTIFIER. If it does, update it instead of creating a duplicate.

Search for incomplete Asana tasks assigned to someone other than TARGET_USER_IDENTIFIER.

If project limits are provided, restrict the scan to those projects. Otherwise scan the full workspace.

Only include tasks where TARGET_USER_IDENTIFIER is involved, meaning one or more of:
- the user is a collaborator on the task
- the user was mentioned in a recent comment or story
- there is an incomplete subtask assigned to the user
- a custom field references the user by name

For each included task, determine whether it should be labeled:
- Needs my action
- FYI / watching

Mark a task as Needs my action if any deterministic rule clearly applies:
- there is an incomplete subtask assigned to the user
- a recent comment mentions the user
- a recent comment asks the user for input, review, approval, decision, answer, or next step
- the latest unresolved request directed at the user happened after the user's last reply

Only use an LLM if the recent comments are ambiguous. If you use one, constrain it to structured JSON with:
- needs_my_action
- confidence
- reason

Create or update the summary task description using this format:

Friday summary of open tasks I’m involved in that are assigned to someone else.

Needs my action
- (TASK_URL) — Assignee: ASSIGNEE_NAME — Due: DUE_DATE_OR_NONE
Reason: SHORT_REASON

FYI / watching
- (TASK_URL) — Assignee: ASSIGNEE_NAME — Due: DUE_DATE_OR_NONE
Reason: SHORT_REASON

If there are no matching tasks, still create or update the summary task and write:
No open tasks assigned to others currently appear to need my attention.

Use direct Asana task links for each item:
(https://app.asana.com/0/WORKSPACE_GID/TASK_GID)

Return the final summary task link and any notable follow-up suggestions.
```

## Engineering Expectations

If the user asks for a standalone Python implementation instead of a direct Asana skill automation, the implementation should include:

- Python
- clean modular structure
- README
- `.env.example`
- pagination support
- retries and logging
- dry-run mode
- unit tests for classification logic
- scheduler instructions for cron or GitHub Actions

Nice to have:

- configurable task title
- configurable lookback window
- optional project filtering

## Caveats

- Involvement does not always mean action is required.
- Mentions in old comments should not outweigh more recent replies.
- Collaborator membership alone is weak evidence; prefer stronger signals first.
- Custom fields that reference a person can be noisy; treat them as involvement signals, not automatic action signals.
- If confidence is low, say so in the reason instead of overstating certainty.

## Validation Checklist

- Confirm the target user resolves correctly.
- Confirm the scan excludes tasks assigned to the target user.
- Confirm only incomplete tasks are considered.
- Confirm duplicate detection checks title plus due date.
- Confirm both sections are present in the summary.
- Confirm every listed task includes a direct Asana link.
- Confirm the fallback message appears when there are no matching tasks.
- Confirm LLM usage is skipped when deterministic rules are sufficient.

## Example Placeholder Set

- `TARGET_USER_IDENTIFIER`: `me`
- `WORKSPACE_GID`: `WORKSPACE_GID`
- `TASK_TITLE`: `Friday Follow-Up Summary`

## Relationship To Cookbook

This file is the full spec.
The shorter discovery entry lives in `references/recipes.md`.
