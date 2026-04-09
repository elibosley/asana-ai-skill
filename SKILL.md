---
name: asana
description: Use when reading or updating Asana data through the REST API, including tasks, projects, sections, stories/comments, teams, users, tags, attachments, custom fields, and workspace metadata. Best for local automation or one-off Asana admin/workflow tasks where an AI coding agent should make direct API calls with a personal access token. Also use it for higher-level workflows such as daily-briefing command centers, my-tasks-organizer AI-gated My Tasks triage backed by the inbox-cleanup helper, close-out-sections cleanup, assigned-work working-set triage, manager summary rollups, and recurring follow-up summaries.
---

# Asana

## Overview

This skill provides a local, reusable Asana API wrapper plus concise references for the common read/write flows in Asana.

Use it when you need to inspect or mutate Asana objects directly from an AI coding agent instead of clicking through the UI.
On first run, the helper now includes a `skill_advertising` block in discovery-style command output so the agent can see My Tasks size, recommended starting points, and the highest-value commands for this workspace.

## Default Context

- Skill root: the installed `asana` skill directory
- API helper: `scripts/asana_api.py`
- Preferred token file: `~/.agent-skills/asana/asana_pat`
- Preferred defaults/context file: `~/.agent-skills/asana/asana-context.json`
- Preferred cache file: `~/.agent-skills/asana/asana-cache.json`
- Overrides: `ASANA_TOKEN_FILE`, `ASANA_CONTEXT_FILE`, and `ASANA_CACHE_FILE`

The helper reads the PAT from `ASANA_ACCESS_TOKEN` first, then falls back to the shared local token file, then the legacy `~/.codex/skills-data/asana/asana_pat` path, and finally to the legacy in-skill `.secrets/asana_pat` path.

## Workflow

1. Before substantial work, run `python3 scripts/update_skill.py --quiet --best-effort` so the skill can pick up fixes from the shared repo without blocking the task if the network or git auth is unavailable.
2. Read `references/cli-reference.md` first for the exact parser-derived command surface. Prefer it over ad hoc `--help` calls or rereading `scripts/asana_api.py` unless you are actively changing the CLI.
3. Read `references/api-overview.md` for auth, request shape, pagination, and the endpoint map.
4. Read `references/recipes.md` when you need ready-made commands for common operations.
5. Use `python3 scripts/asana_api.py ...` for API calls.
6. When you need to plan work from a single Asana ticket, prefer `task-bundle` first because it pulls task fields, comments, attachments, and project workflow context together in one call.
7. The lookup-style read commands now accept one or many gids directly. Pass a single gid or a comma-separated / space-separated list, and expect a consistent wrapper payload with `command`, `count`, and `items`.
8. When you need assigned work inside a project, prefer `project-assigned-tasks` over `project-tasks`. It searches the workspace by project + assignee, includes matching subtasks, and enriches subtasks with parent section context when the subtask itself has no direct project membership.
9. When the user wants a pull list, triage doc, or "what should I work on now?" answer from assigned project tasks, use a two-pass workflow:
   - First run `project-assigned-tasks` with contextual flags so you get section order, section position, recent comments, attachments, and parent context in one payload.
   - Then run `task-bundle` only for the short list of tasks that actually look like active implementation work.
   - Do not stop at a raw checklist. Produce a contextual working set that separates:
     - implemented / QA-only
     - active code-now
     - needs repro or screenshots before code
     - backlog / no-code / workflow cleanup
10. For triage-style docs, explicitly state whether the document is a raw Asana snapshot or an implementation-ready plan. If it is only a snapshot, say so and add a "current engineering read" section rather than presenting the whole list as one coding scope.
11. Do not rely on `project-tasks` alone for "my tasks in project" pulls. Asana project task lists can miss assigned subtasks that still matter for implementation work.
12. The helper now keeps a local entity cache for workspaces, teams, projects, users, and tags. Commands like `whoami`, `workspaces`, `teams`, `projects`, `users`, `tags`, and `project-assigned-tasks` refresh that cache automatically.
13. When a command accepts a user identifier such as `--assignee` or follower values, prefer exact gids when you already have them, but cached exact user names and emails now work too.
14. For writes, inspect the current object first unless the user already provided the exact target GID and desired mutation.
15. Prefer task/project comments (`stories`) for status notes instead of overwriting task descriptions unless the user asked for that.
16. Treat section names and section order as raw workflow context. Do not assume a given column means “done” unless the user or surrounding project context says so.
17. For any AI-authored comment or AI-authored task-note update, begin the message with the heading `AI MESSAGE DISCLAIMER`.
18. Use rich-text HTML fields for AI-authored updates whenever formatting matters:
   - Task comments/stories: `html_text`
   - Task descriptions/notes: `html_notes`
19. Do not paste Markdown-style bullets or escaped `\n` sequences into plain `text` fields when the message needs headings, lists, or paragraphs. Prefer proper HTML structure.
20. Before posting or updating an AI-authored message, sanity-check how it will render in Asana: use block-style sections for narrative/status lines, `<strong>` for labels, and `<ul><li>` only for actual lists rather than relying on Markdown.
21. The wrapper supports rich-text comments, but not an explicit mention flag. When the user wants an `@mention`, first check whether Asana will accept the mention token in `html_text`; if not, fall back to the raw stories endpoint with the mention format Asana expects.
22. After any write that creates or updates a task or story, include the returned Asana `review_url` in your user-facing reply so the user can click straight into the updated object. For story writes, also surface `target_review_url` when helpful so the user can review the parent task.
23. The helper auto-normalizes AI disclaimer messages that arrive as one inline HTML blob or as the older single-list disclaimer format, and it now compacts AI-authored rich text before posting so indentation whitespace does not create phantom empty bullets in Asana.
24. For My Tasks intake cleanup, prefer the `my-tasks-organizer` companion skill or the underlying `inbox-cleanup` helper over manual section shuffling. Treat it as the default "work through my tasks with me" mechanism, but with an AI gate: the first run should fetch context and emit a snapshot plus plan template, not move tasks immediately.
25. `inbox-cleanup` should default to the `Recently assigned` My Tasks section unless the user explicitly asks for a wider sweep such as `--all-open` or extra `--source-section` values.
26. Use the helper's `skill_advertising` block when present. It summarizes My Tasks size, flags when `Recently assigned` is large enough to justify `inbox-cleanup`, and highlights other useful commands such as `task-bundle`, `project-assigned-tasks`, and `search-tasks`.
27. The AI should define the high-level inbox categories first. Do not let Python heuristics pick the final categories or target sections by themselves.
28. The desired `inbox-cleanup` output is a reviewed JSON plan: category definitions, per-task bucket decisions, specific `ask_user` questions for ambiguous tasks, and concrete section targets for the high-confidence tasks.
29. The helper's snapshot includes legacy task-read hints, but those are only hints for planning. The final bucket decision should come from the AI-authored plan JSON.
30. When applying a plan, move only tasks whose plan entries explicitly say `decision: "bucket"`. Leave `ask_user` and `leave_as_is` tasks untouched, and leave low-confidence decisions untouched unless the caller passes `--include-low-confidence`.
31. The AI should still reason about the work, not just the filing: what the task really is, what should happen next, what user input is missing, and whether the inbox needs a new category or section that does not already exist.
32. When the user wants to retire old personal sections, prefer `close-out-sections` over ad hoc manual moves. It can preview exact source sections, move all tasks or only completed/incomplete tasks into a destination section, and only deletes the source section after it is actually empty.
33. Treat some My Tasks columns as potentially undeletable even after they are empty. In particular, `Recently assigned` can usually be drained to zero tasks, but Asana may still refuse to remove the column, so present that outcome as "emptied but not removable" rather than retrying indefinitely.
34. When the user wants a full morning overview instead of a filing pass, prefer `daily-briefing`. Treat it as a read-only AI-gated workflow: the helper emits a snapshot plus plan template, but the agent should create the plan itself and show the user the rendered result rather than making the user fill in the intermediate JSON.
35. The AI should decide which tasks are actually actionable today and which briefing buckets matter. Do not let Python heuristics choose the final morning queue for `daily-briefing`.
36. The desired `daily-briefing` output is a reviewed JSON plan where the AI also authors the final human-facing markdown directly in `final_markdown`. Python should validate and pass that markdown through, not own the briefing template.
37. When the user wants a weekly or manager-facing summary for another person's assigned work, prefer a search-and-summarize workflow over board-only views: search by assignee inside the target workspace or project, bucket tasks into recently completed, in progress, and blocked/stalled based on completion date, due date, and recent activity, then create a single manager-facing follow-up task or note with direct task links and recommended follow-up messages.
38. For manager rollups, keep the output operational rather than narrative. The default useful deliverable is one concise summary artifact with clearly labeled sections, direct Asana task links, and draft follow-up prompts for anything that is active, blocked, waiting on someone else, or appears to need manager input.
39. When the user wants a recurring personal follow-up summary for tasks they are involved in but do not own, prefer an involvement-scan workflow: search for incomplete tasks assigned to others, detect involvement through collaborators, recent mentions, assigned subtasks, or custom-field references, classify each task into `Needs my action` or `FYI / watching`, and create or update one summary task in the user's My Tasks with direct task links and short reasons.
40. For involvement scans, use deterministic rules first and only use an LLM when the task comments are ambiguous. If an LLM is needed, constrain it to structured output with `needs_my_action`, `confidence`, and `reason` so the final summary stays auditable and stable across runs.
41. For long automation asks, keep the abbreviated guidance in `references/recipes.md`, but prefer dedicated full-body specs in `references/automations/` so the complete prompt, placeholders, output contract, scheduling notes, and edge cases live in one place. When a recipe has a matching automation spec, load that full spec before executing or editing the automation.
42. If the task changes this skill repo itself, treat it as a shipped skill update unless the user explicitly says not to release it yet.
43. Before committing or pushing any skill change, run `python3 scripts/check_release.py`. Do not push until it passes.
44. If `check_release.py` fails because release metadata is missing, run `python3 scripts/bump_version.py --part auto --title "Short release title"`. Let the helper choose the semantically correct bump from the current diff unless the user explicitly wants an override. Replace the scaffold line in `CHANGELOG.md` with a real user-facing summary, rerun `python3 scripts/check_release.py`, then commit and push.
45. Never leave the top changelog entry on the placeholder text `Describe the user-visible change here.` If you bumped the version, you own writing the matching release note before you finish.
46. When the user wants a single sorter label on My Tasks such as `Quick Win`, `Delegate`, `Close Out`, `Deep Work`, `Waiting`, or `Needs Clarity`, treat those as native Asana task tags unless the workspace explicitly uses a custom field instead.
47. For one-of-many sorter tags, prefer `python3 scripts/asana_api.py set-task-sorting-tag <task_gid> "<label>"` over ad hoc tag mutation. That command removes only the other sorter tags, preserves unrelated project tags, and leaves the task untouched when the desired sorter tag is already correct.
48. `add-task-tag` and `remove-task-tag` now accept exact tag names as well as raw gids. Use exact names when the user supplied human labels and the tag cache or workspace tag list can resolve them.
49. If the user asks for a full tag-based My Tasks pass, read the task title, description, existing sorter tags, and any blocking context first, then apply exactly one sorter tag per task while preserving every non-sorter tag.

## AI Message Format

Use this structure for AI-authored comments and task-note updates.
Asana rich text does not support heading tags like `<h1>` or paragraph tags like `<p>` in API writes, so the disclaimer heading should be rendered with `<strong>` inside the root `<body>` instead:

```html
<body>
  <strong>AI MESSAGE DISCLAIMER</strong>
  <blockquote>This message was generated by AI to summarize implementation status and verification.</blockquote>
  <strong>Status:</strong>
  <blockquote>Pushed to branch <code>branch-name</code>.</blockquote>
  <strong>Fixed:</strong>
  <ul>
    <li>First concrete change.</li>
    <li>Second concrete change.</li>
  </ul>
  <strong>Verification:</strong>
  <ul>
    <li><code>pnpm --filter ...</code></li>
  </ul>
</body>
```

Keep the disclaimer brief, factual, and clearly separated from the work summary.
Prefer blockquote-style narrative sections plus real lists over one giant bullet list.
Supported write-safe tags for normal status updates are: `<body>`, `<strong>`, `<em>`, `<u>`, `<s>`, `<code>`, `<ol>`, `<ul>`, `<li>`, `<a>`, `<blockquote>`, and `<pre>`.

## Common Commands

```bash
python3 scripts/asana_api.py whoami
python3 scripts/asana_api.py workspaces
python3 scripts/asana_api.py teams
python3 scripts/asana_api.py users
python3 scripts/asana_api.py show-cache
python3 scripts/check_release.py
python3 scripts/bump_version.py --part auto --title "Short release title"
python3 scripts/asana_api.py workspace-custom-fields
python3 scripts/asana_api.py projects --team <team_gid>
python3 scripts/asana_api.py project-tasks <project_gid>
python3 scripts/asana_api.py project-assigned-tasks <project_gid> --completed false
python3 scripts/asana_api.py project-assigned-tasks <project_gid> --completed false --include-task-position --include-comments --comment-limit 3 --include-attachments
python3 scripts/asana_api.py sections <project_gid>
python3 scripts/asana_api.py board <project_gid>
python3 scripts/asana_api.py board <project_gid> --context
python3 scripts/asana_api.py trigger-rule <trigger_identifier> --task <task_gid>
python3 scripts/asana_api.py trigger-rule <trigger_identifier> --task <task_gid> --action-data status=approved --action-data reviewer=jane
python3 scripts/asana_api.py task <task_gid>
python3 scripts/asana_api.py story <story_gid>
python3 scripts/asana_api.py task-bundle <task_gid> --project-gid <project_gid>
python3 scripts/asana_api.py task-status <task_gid>
python3 scripts/asana_api.py task-stories <task_gid>
python3 scripts/asana_api.py task-comments <task_gid>
python3 scripts/asana_api.py task-custom-fields <task_gid>
python3 scripts/asana_api.py inbox-cleanup
python3 scripts/asana_api.py inbox-cleanup --snapshot-file /tmp/asana-inbox-snapshot.json --plan-template-file /tmp/asana-inbox-plan.json
python3 scripts/asana_api.py inbox-cleanup --all-open --max-tasks 50
python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json
python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json --apply
python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json --apply --include-low-confidence
python3 scripts/asana_api.py daily-briefing
python3 scripts/asana_api.py daily-briefing --snapshot-file /tmp/asana-daily-briefing-snapshot.json --plan-template-file /tmp/asana-daily-briefing-plan.json
python3 scripts/asana_api.py daily-briefing --plan-file /tmp/asana-daily-briefing-plan.json
python3 scripts/asana_api.py daily-briefing --plan-file /tmp/asana-daily-briefing-plan.json --markdown
python3 scripts/asana_api.py close-out-sections <project_gid> --section "Old Section" --move-to "Work Completed" --completed-mode completed
python3 scripts/asana_api.py close-out-sections <project_gid> --section "Old Section" --move-to "Work Completed" --completed-mode completed --apply
python3 scripts/asana_api.py create-task --name "Follow up" --project <project_gid>
python3 scripts/asana_api.py create-task --name "Follow up" --project <project_gid> --assignee "Exact User Name"
python3 scripts/asana_api.py update-task <task_gid> --completed true --assignee "user@example.com"
python3 scripts/asana_api.py comment-task <task_gid> --text "Status update"
python3 scripts/asana_api.py create-section <project_gid> --name "Ready"
python3 scripts/asana_api.py add-task-followers <task_gid> me
python3 scripts/asana_api.py add-task-tag <task_gid> <tag_gid>
python3 scripts/asana_api.py add-task-tag <task_gid> "Deep Work"
python3 scripts/asana_api.py set-task-sorting-tag <task_gid> "Needs Clarity"
python3 scripts/asana_api.py add-task-dependencies <task_gid> <other_task_gid>
python3 scripts/asana_api.py batch --actions '[{"method":"get","relative_path":"/users/me"}]'
```

## Workflow Analysis

When the user asks about workflow optimizations, project health, or automation rules:

1. Run `board <project_gid> --context` to get the enriched board snapshot with stats.
2. Read `references/workflow-patterns.md` for bottleneck detection patterns and rule templates.
3. Analyze the `context` key in the output — look for section pile-ups, stale tasks, low custom field coverage, unassigned tasks, and missing due dates.
4. Recommend specific Asana rules with step-by-step UI creation instructions from the patterns reference.
5. If the user has existing rules with "Incoming web request" triggers, use `trigger-rule` to trigger them programmatically.

Note: Asana does not expose rule creation via API. Rules must be created in the Asana web UI. The workflow advisor analyzes board context and recommends rules — it cannot create them automatically.

## Guardrails

- Never print the PAT in output.
- Keep file uploads and external URL attachments explicit; do not guess attachment URLs.
- When changing membership-like relationships such as followers, tags, dependencies, or project membership, prefer the dedicated endpoints over full-object replacement.
- When using the generic `request` subcommand, remember that JSON bodies are wrapped in `{"data": ...}` by default unless `--no-wrap-data` is passed.
- Use `completed` as the canonical completion flag. Treat column/section names as additional context to report, not as an automatic status mapping.
- For project pull lists, do not present the raw assigned-task response as the final answer. Interpret the enriched context and tell the user which tasks are already done, which are true code work, and which should be closed or re-scoped first.

## References

- Parser-derived CLI reference: `references/cli-reference.md`
- Machine-readable CLI spec: `references/cli-reference.json`
- Core API guide: `references/api-overview.md`
- Common command cookbook: `references/recipes.md`
- Full automation specs: `references/automations/`
- Workflow patterns and rule templates: `references/workflow-patterns.md`
