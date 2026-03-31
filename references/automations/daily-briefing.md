# Daily Briefing Workflow Spec

## Purpose

Render a standardized, easy-to-scan morning command center for open My Tasks.

This is the long-form source of truth for `daily-briefing`.
Use it when the agent should execute, edit, review, or schedule this workflow for Codex or Claude.

## Use When

- The user asks, `what should I focus on this morning?`
- The user wants a command center instead of a filing pass.
- The user wants a read-only daily overview of open My Tasks.
- The workflow should standardize the same output shape across Codex and Claude.

## Works With

- `python3 scripts/asana_api.py daily-briefing`
- `python3 scripts/asana_api.py daily-briefing --markdown`
- `python3 scripts/asana_api.py show-context`
- `python3 scripts/asana_api.py show-cache`

## Inputs

Required placeholders:

- none when using the default authenticated user context

Optional placeholders:

- `MAX_TASKS`, default helper behavior unless the user wants a cap
- `OUTPUT_MODE`, prefer `--markdown` for human-readable summaries
- `FOCUS_BIAS`, optional note from the user such as "ship-focused", "verification-heavy", or "broad morning overview"

## Output Contract

The workflow is read-only.
It should not move tasks, edit tasks, or create comments.

Preferred output mode:

- markdown

Required output characteristics:

- one concise morning overview
- direct task links for every surfaced task
- explicit bucket headings in a stable order
- enough context to explain why a task is in that bucket
- suppression of low-signal admin noise into the background bucket

## Standard Bucket Order

Always prefer this bucket order unless the user asks for a different layout:

1. `Execute Now`
2. `Release / Ship Watch`
3. `Needs Verification`
4. `Needs Follow-Up`
5. `Likely Ready To Close`
6. `Background / Not Today`

The exact bucket names should stay stable across Codex and Claude outputs unless the user explicitly asks for different naming.

## Section Semantics

### Execute Now

Tasks where the user is the clear driver and the next step is implementation or direct execution today.

Typical signals:

- open task
- recent activity
- no done-like workflow state
- actionable next step is clear

### Release / Ship Watch

Tasks that already have implementation progress and now mostly require release awareness, coordination, or monitoring.

Typical signals:

- task has PR, branch, ship, release, staging, or deployment context
- project column already suggests `Done`, `Test`, `Staging`, `QA`, `Production`, or similar

### Needs Verification

Tasks where the likely next step is testing, checking results, confirming behavior, or verifying a rollout.

Typical signals:

- waiting on QA
- user needs to inspect output
- task moved into a verification-like column

### Needs Follow-Up

Tasks where the user needs to ask a question, unblock someone, answer a request, or coordinate with another person.

Typical signals:

- waiting on another person
- recent request for response
- stale-but-not-dead task where follow-up is the right next move

### Likely Ready To Close

Tasks that appear effectively done or superseded and probably need confirmation plus closure.

Typical signals:

- evidence of completion
- no remaining visible work
- task still open for workflow reasons only

### Background / Not Today

Tasks that should stay visible in the morning overview but should not drive today's work.

Typical signals:

- admin
- reminders
- long-horizon planning
- low-signal backlog
- training or housekeeping

## Deterministic Rules

Use workflow state and helper context first.

Important rules:

- If a task has code or PR context but its project column already says `Done`, `Test`, `Staging`, `QA`, `Production`, or similar, do not place it in `Execute Now`.
- Move done-like work into `Release / Ship Watch` or `Needs Verification` instead.
- Keep the command center broad, but push low-signal admin and reminder tasks into `Background / Not Today`.
- Do not infer that a task is complete from section names alone; use `completed` plus surrounding context.

## Standard Output Shape

Recommended markdown structure:

```text
# Morning Briefing

One short paragraph on the overall shape of the day.

## Execute Now
- [Task name](TASK_URL) — one-line reason

## Release / Ship Watch
- [Task name](TASK_URL) — one-line reason

## Needs Verification
- [Task name](TASK_URL) — one-line reason

## Needs Follow-Up
- [Task name](TASK_URL) — one-line reason

## Likely Ready To Close
- [Task name](TASK_URL) — one-line reason

## Background / Not Today
- [Task name](TASK_URL) — one-line reason
```

Each task line should include:

- direct task link
- brief explanation
- only the most relevant context

Do not turn the output into a raw dump of all open tasks.

## Prompt Template

```text
Use the installed Asana skill.

Run the daily-briefing workflow for the current user and prefer markdown output.

Return a read-only morning command center for open My Tasks.

Use these bucket names and keep them in this order:
1. Execute Now
2. Release / Ship Watch
3. Needs Verification
4. Needs Follow-Up
5. Likely Ready To Close
6. Background / Not Today

For every surfaced task, include a direct task link and a short reason.

Keep the output broad but opinionated:
- show important non-code queues too
- suppress admin, reminder, and low-signal tasks into Background / Not Today
- if a task has PR or code context but its project state already says Done, Test, Staging, QA, or Production, do not put it in Execute Now

Do not mutate tasks, move sections, or add comments.

Format the final output in markdown so it is easy to scan in both Codex and Claude.
```

## Invocation Short Forms

These are good short user instructions that should reliably map to this spec:

- `Use the Asana skill and run the full spec in references/automations/daily-briefing.md.`
- `Run the daily briefing spec for me in markdown.`
- `Use the daily briefing workflow spec and give me the full morning command center.`

## Scheduling Guidance

Good default schedule:

- weekday mornings
- user's local timezone
- one run early enough to shape the workday

Good recurring uses:

- every workday morning
- Monday-through-Friday at a fixed time

## Standardization Notes For Codex And Claude

To keep outputs comparable across tools:

- prefer markdown
- keep bucket names stable
- keep bucket order stable
- keep each task explanation to one line when possible
- avoid nested bullet hierarchies
- keep the opening overview short

If the user asks for a different format, follow that request explicitly.

## Caveats

- My Tasks can be large and noisy; the briefing should summarize, not dump.
- Workflow columns are strong signals but not absolute truth.
- Some tasks may fit multiple buckets; choose the one that best reflects the next action.
- The best daily briefing is opinionated but still conservative about hidden assumptions.

## Validation Checklist

- Confirm the workflow is read-only.
- Confirm the output uses the standard bucket order.
- Confirm each surfaced task includes a direct link.
- Confirm done-like workflow states do not end up in `Execute Now`.
- Confirm low-signal tasks are suppressed into `Background / Not Today`.
- Confirm the output is concise enough to scan quickly in the morning.

## Relationship To Cookbook

This file is the full spec.
The shorter discovery entry lives in `references/recipes.md`.
