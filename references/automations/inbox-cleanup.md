# Inbox Cleanup Workflow Spec

## Purpose

Run `inbox-cleanup` as a personal PM pass over My Tasks intake.

This is the long-form source of truth for `inbox-cleanup`.
Use it when the agent should execute, edit, review, or schedule this workflow for Codex or Claude.

## Use When

- The user asks to sort or triage My Tasks intake.
- The user wants to know what each task really is and what should happen next.
- The workflow should propose next actions, TODOs, and immediate AI opportunities.
- The caller may want optional AI-authored task comments, but only when privacy rules allow it.

## Works With

- `python3 scripts/asana_api.py inbox-cleanup`
- `python3 scripts/asana_api.py inbox-cleanup --apply`
- `python3 scripts/asana_api.py inbox-cleanup --manager-comments`
- `python3 scripts/asana_api.py inbox-cleanup --comment-research-todos --apply`
- `python3 scripts/asana_api.py show-context`
- `python3 scripts/asana_api.py show-cache`

## Inputs

Required placeholders:

- none when using the default authenticated user context

Optional placeholders:

- `SOURCE_SECTION`, default `Recently assigned`
- `ALL_OPEN`, when the user wants a wider sweep
- `MAX_TASKS`
- `APPLY_MODE`, preview by default, mutate only when explicitly requested
- `COMMENT_MODE`, one of:
  - none
  - manager-comments
  - comment-research-todos

## Output Contract

The workflow should produce a triage-oriented result, not just a section shuffle.

Required outputs per task:

- work type
- suggested next action
- TODO list
- whether AI can execute now
- what the user should be asked before acting
- `active_ai_action` when available

Allowed `active_ai_action` patterns:

- `ask_to_execute_now`
- `ask_to_verify`
- `ask_to_follow_up`
- `ask_to_close`
- `no_ai_action`

## Default Scope

Default to the `Recently assigned` My Tasks section unless the user explicitly asks for:

- `--all-open`
- additional source sections
- a broader cleanup pass

## Deterministic Rules

Use My Tasks and task context first.

Important rules:

- treat `inbox-cleanup` as a personal PM pass, not as a blind sorter
- do not complete tasks as part of the cleanup
- move tasks into review sections only when the classification is clear
- keep the default scope narrow
- use linked PRs, recent comments, and workflow context to infer next actions

## Comment Safety Rules

AI-authored comments are optional and should be conservative.

### Manager Comments

Only post manager-style comments when the task looks truly private:

- no shared project context that suggests a wider audience
- no parent-task context that broadens visibility
- no non-assignee followers or collaborators
- no comment history from anyone other than the assignee

### Research TODO Comments

Use `--comment-research-todos` when the user wants investigation prompts without a broader PM-style narrative.

## Standard Output Shape

Recommended summary structure:

```text
# Inbox Cleanup

Short paragraph on the state of intake.

## Task Name
- Type: WORK_TYPE
- Suggested next action: ACTION
- TODOs: ...
- AI can help now: yes/no
- Ask user: QUESTION
- Active AI action: ask_to_execute_now
```

If the user asked for a write mode:

- clearly state whether the run is preview or apply
- clearly state whether comments were posted

## Prompt Template

```text
Use the installed Asana skill.

Run the inbox-cleanup workflow for the current user.

Default to the Recently assigned My Tasks section unless I explicitly ask for a broader sweep.

Treat this as a personal PM pass, not just a section-move pass.

For each task, tell me:
- what this task really is
- what should happen next
- the TODO list
- whether AI can execute now
- what question to ask me before acting
- the active_ai_action, if one is apparent

Do not complete tasks.

Only move tasks into review sections when the classification is clear.

Only post AI-authored comments if I explicitly ask for them and the task looks truly private.
```

## Invocation Short Forms

- `Use the Asana skill and run the full spec in references/automations/inbox-cleanup.md.`
- `Run inbox-cleanup as a personal PM pass for me.`
- `Use the inbox-cleanup spec and tell me what each task is, what happens next, and what AI can do now.`

## Scheduling Guidance

Good recurring uses:

- morning intake sweeps
- end-of-day review passes
- weekly cleanup windows

Use scheduled automation carefully if write modes are enabled.
Preview-only scheduled runs are safer than comment-posting scheduled runs.

## Caveats

- My Tasks privacy heuristics are conservative by design.
- Shared project tasks can look personal at first glance; do not over-post.
- A task may need human context even when the next action looks obvious.
- Section moves are not the goal by themselves; the classification is the real output.

## Validation Checklist

- Confirm the run stayed inside the requested My Tasks scope.
- Confirm tasks were not completed.
- Confirm each surfaced task has next-action guidance.
- Confirm write modes only ran when requested.
- Confirm comments, if any, were posted only on private-looking tasks.
- Confirm `active_ai_action` is populated only when the evidence supports it.

## Relationship To Cookbook

This file is the full spec.
The shorter discovery entry lives in `references/recipes.md`.
