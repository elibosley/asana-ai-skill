# Inbox Cleanup Workflow Spec

## Purpose

Run `inbox-cleanup` as a personal PM pass over My Tasks intake.

The workflow is only useful if it answers the real question:

- what is this task actually asking for
- what should happen next
- what can AI do right now
- what should be asked back to the user before acting

Section moves are optional consequences of that reasoning, not the goal.

## Core Principle

`inbox-cleanup` must not behave like a blind sorter.

It should first determine the task read, then the next move, and only then decide whether the task belongs in:

- `Review: Needs Next Action`
- `Review: Needs Verification`
- `Review: Waiting On Others`
- `Review: Likely Ready To Close`
- `Review: Backlog Cleanup`

If the output cannot explain why the task landed in a bucket, the workflow is not done.

## Use When

- The user says “clean up my inbox” or “triage My Tasks”.
- The user wants a PM-style read on intake, not raw Asana JSON.
- The user wants to know which tasks are worth executing now versus verifying, following up, or parking.
- The caller may optionally want safe AI-authored comments after the triage.

## Works With

- `python3 scripts/asana_api.py inbox-cleanup`
- `python3 scripts/asana_api.py inbox-cleanup --apply`
- `python3 scripts/asana_api.py inbox-cleanup --manager-comments`
- `python3 scripts/asana_api.py inbox-cleanup --comment-research-todos --apply`

## Inputs

Required placeholders:

- none when using the default authenticated user context

Optional placeholders:

- `SOURCE_SECTION`, default `Recently assigned`
- `ALL_OPEN`, when the user wants a wider sweep
- `MAX_TASKS`
- `APPLY_MODE`, preview by default
- `COMMENT_MODE`, one of:
  - none
  - manager-comments
  - comment-research-todos

## Required Reasoning Per Task

The workflow should read:

- task title
- notes / description
- project and section context
- due date
- recent comments
- PR links or inline `PR #123` references
- docs / spec / spreadsheet links

Then it should produce:

- `task_read`
  - one or two sentences on what the task really is
  - example: “This is a scoping/decision task, not implementation yet.”
- `classification_basis`
  - why it landed in the chosen bucket
  - example: “Recent comments plus `Test` project state point to verification, not net-new work.”
- `next_action`
  - the concrete next move
- `todo_items`
  - a short, specific checklist
- `ask_user`
  - the one question that would unblock action fastest
- `ai_help_now`
  - boolean
- `ai_help_summary`
  - what AI can do immediately if the user says yes
- `active_ai_action`
  - one of:
    - `ask_to_execute_now`
    - `ask_to_verify`
    - `ask_to_follow_up`
    - `ask_to_close`
    - `no_ai_action`

## Behavioral Rules

### 1. Determine the task read before moving anything

Every surfaced task must have a real read of the work, not just a category label.

Good:

- “This is a writing/recommendation task. The missing artifact is the first draft.”
- “This no longer looks like implementation. It looks like verification against PR #2593.”
- “This is blocked on another person or team; the next move is a concrete unblock ask.”

Bad:

- “Implementation task”
- “Needs next action”
- “Follow up”

### 2. Separate AI execution from comment safety

A shared task can still be a good `ask_to_execute_now` candidate.

Do not suppress AI execution recommendations just because:

- the task is in a shared project
- there are other followers
- manager comments are disabled

Those conditions should only block auto-commenting, not the recommendation itself.

### 3. Prefer deliverables over vague verbs

When titles contain verbs like:

- `draft`
- `decide`
- `clarify`
- `validate`
- `scope`
- `recommend`

the next action should name the missing artifact:

- memo
- recommendation
- scoped proposal
- close-out note
- unblock message

### 4. Verification is not execution

Tasks that mention:

- `Test`
- `QA`
- `staging`
- `preview`
- `beta`
- `PR #123`
- “please test”
- screenshots or shipped evidence

should usually become verification work, not default implementation work.

### 5. Waiting is not backlog

If the strongest signal is dependency or handoff, the workflow should say:

- who is blocking
- what should be asked
- what date/checkpoint should be recorded

Do not dump these into a generic “follow up later” bucket.

## Output Contract

The output should be useful enough that a human can act on it immediately.

Minimum useful shape:

```text
# Inbox Cleanup

Short paragraph on the state of intake and whether this is preview or apply.

## Task Name
- Task read: what this really is
- Why this bucket: why it landed there
- Suggested next action: the concrete next move
- TODOs: specific checklist
- Ask user: the one missing question
- AI can help now: yes/no + how
- Active AI action: ask_to_execute_now
```

If the workflow cannot fill these fields, it should say the task is under-specified instead of pretending otherwise.

## Write Mode Rules

Preview is the default.

In `--apply` mode:

- move tasks only after the task read and classification are clear
- do not complete tasks
- do not post manager comments unless explicitly requested
- keep AI-authored comments conservative

## Comment Safety Rules

### Manager Comments

Only post manager-style comments when the task looks truly private:

- no shared project context that suggests a wider audience
- no parent-task context that broadens visibility
- no non-assignee followers or collaborators
- no comment history from anyone other than the assignee

### Research TODO Comments

Use `--comment-research-todos` when the user wants investigation prompts without a broader PM-style narrative.

## Prompt Template

```text
Use the installed Asana skill.

Run the inbox-cleanup workflow for the current user.

Default to the Recently assigned My Tasks section unless I explicitly ask for a broader sweep.

Treat this as a personal PM pass, not a section-sorting pass.

For each task, determine:
- what this task really is
- why it belongs in this bucket
- what should happen next
- the TODO list
- what you need to ask me before acting
- whether AI can help now, and how
- the active_ai_action

Only after that should you move the task into a review bucket.

Do not complete tasks.

Only post AI-authored comments if I explicitly ask for them and the task is private enough.
```

## Invocation Short Forms

- `Use the Asana skill and run the full spec in references/automations/inbox-cleanup.md.`
- `Run inbox-cleanup as a personal PM pass for me.`
- `Tell me what each intake task actually is and what should happen next.`
- `Use inbox-cleanup, but do not stop at reclassification.`

## Scheduling Guidance

Good recurring uses:

- morning intake sweeps
- end-of-day review passes
- weekly cleanup windows

Preview-only schedules are safer than scheduled write modes.

## Validation Checklist

- Confirm the run stayed inside the requested My Tasks scope.
- Confirm tasks were not completed.
- Confirm every surfaced task has `task_read`, `classification_basis`, `next_action`, `ask_user`, and AI-help guidance.
- Confirm section moves happened only after reasoning.
- Confirm comments, if any, were posted only on private-looking tasks.
- Confirm `active_ai_action` reflects the real next move, not just comment privacy.

## Relationship To Cookbook

This file is the full workflow spec.
The shorter discovery entry lives in `references/recipes.md`.
