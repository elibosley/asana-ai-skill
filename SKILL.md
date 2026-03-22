---
name: asana
description: Use when reading or updating Asana data through the REST API, including tasks, projects, sections, stories/comments, teams, users, tags, attachments, custom fields, and workspace metadata. Best for local automation or one-off Asana admin/workflow tasks where an AI coding agent should make direct API calls with a personal access token.
---

# Asana

## Overview

This skill provides a local, reusable Asana API wrapper plus concise references for the common read/write flows in Asana.

Use it when you need to inspect or mutate Asana objects directly from an AI coding agent instead of clicking through the UI.

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
2. Read `references/api-overview.md` for auth, request shape, pagination, and the endpoint map.
3. Read `references/recipes.md` when you need ready-made commands for common operations.
4. Use `python3 scripts/asana_api.py ...` for API calls.
5. When you need to plan work from a single Asana ticket, prefer `task-bundle` first because it pulls task fields, comments, attachments, and project workflow context together in one call.
6. When you need assigned work inside a project, prefer `project-assigned-tasks` over `project-tasks`. It searches the workspace by project + assignee, includes matching subtasks, and enriches subtasks with parent section context when the subtask itself has no direct project membership.
7. When the user wants a pull list, triage doc, or "what should I work on now?" answer from assigned project tasks, use a two-pass workflow:
   - First run `project-assigned-tasks` with contextual flags so you get section order, section position, recent comments, attachments, and parent context in one payload.
   - Then run `task-bundle` only for the short list of tasks that actually look like active implementation work.
   - Do not stop at a raw checklist. Produce a contextual working set that separates:
     - implemented / QA-only
     - active code-now
     - needs repro or screenshots before code
     - backlog / no-code / workflow cleanup
8. For triage-style docs, explicitly state whether the document is a raw Asana snapshot or an implementation-ready plan. If it is only a snapshot, say so and add a "current engineering read" section rather than presenting the whole list as one coding scope.
9. Do not rely on `project-tasks` alone for "my tasks in project" pulls. Asana project task lists can miss assigned subtasks that still matter for implementation work.
10. The helper now keeps a local entity cache for workspaces, teams, projects, users, and tags. Commands like `whoami`, `workspaces`, `teams`, `projects`, `users`, `tags`, and `project-assigned-tasks` refresh that cache automatically.
11. When a command accepts a user identifier such as `--assignee` or follower values, prefer exact gids when you already have them, but cached exact user names and emails now work too.
12. For writes, inspect the current object first unless the user already provided the exact target GID and desired mutation.
13. Prefer task/project comments (`stories`) for status notes instead of overwriting task descriptions unless the user asked for that.
14. Treat section names and section order as raw workflow context. Do not assume a given column means “done” unless the user or surrounding project context says so.
15. For any AI-authored comment or AI-authored task-note update, begin the message with the heading `AI MESSAGE DISCLAIMER`.
16. Use rich-text HTML fields for AI-authored updates whenever formatting matters:
   - Task comments/stories: `html_text`
   - Task descriptions/notes: `html_notes`
17. Do not paste Markdown-style bullets or escaped `\n` sequences into plain `text` fields when the message needs headings, lists, or paragraphs. Prefer proper HTML structure.
18. Before posting or updating an AI-authored message, sanity-check how it will render in Asana: use paragraphs, `<strong>` for labels, and `<ul><li>` for lists rather than relying on Markdown.
19. After any write that creates or updates a task or story, include the returned Asana `review_url` in your user-facing reply so the user can click straight into the updated object. For story writes, also surface `target_review_url` when helpful so the user can review the parent task.

## AI Message Format

Use this structure for AI-authored comments and task-note updates.
Asana rich text does not support heading tags like `<h1>` or paragraph tags like `<p>` in API writes, so the disclaimer heading should be rendered with `<strong>` inside the root `<body>` instead:

```html
<body>
  <strong>AI MESSAGE DISCLAIMER</strong>
  This message was generated by AI to summarize implementation status and verification.
  <strong>Status:</strong> Pushed to branch <code>branch-name</code>.
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
Prefer short paragraphs and proper lists over dense blobs of text.
Supported write-safe tags for normal status updates are: `<body>`, `<strong>`, `<em>`, `<u>`, `<s>`, `<code>`, `<ol>`, `<ul>`, `<li>`, `<a>`, `<blockquote>`, and `<pre>`.

## Common Commands

```bash
python3 scripts/asana_api.py whoami
python3 scripts/asana_api.py workspaces
python3 scripts/asana_api.py teams
python3 scripts/asana_api.py users
python3 scripts/asana_api.py show-cache
python3 scripts/asana_api.py workspace-custom-fields
python3 scripts/asana_api.py projects --team <team_gid>
python3 scripts/asana_api.py project-tasks <project_gid>
python3 scripts/asana_api.py project-assigned-tasks <project_gid> --completed false
python3 scripts/asana_api.py project-assigned-tasks <project_gid> --completed false --include-task-position --include-comments --comment-limit 3 --include-attachments
python3 scripts/asana_api.py sections <project_gid>
python3 scripts/asana_api.py board <project_gid>
python3 scripts/asana_api.py task <task_gid>
python3 scripts/asana_api.py story <story_gid>
python3 scripts/asana_api.py task-bundle <task_gid> --project-gid <project_gid>
python3 scripts/asana_api.py task-status <task_gid>
python3 scripts/asana_api.py task-stories <task_gid>
python3 scripts/asana_api.py task-comments <task_gid>
python3 scripts/asana_api.py task-custom-fields <task_gid>
python3 scripts/asana_api.py create-task --name "Follow up" --project <project_gid>
python3 scripts/asana_api.py create-task --name "Follow up" --project <project_gid> --assignee "Eli Bosley"
python3 scripts/asana_api.py update-task <task_gid> --completed true --assignee "eli@example.com"
python3 scripts/asana_api.py comment-task <task_gid> --text "Status update"
python3 scripts/asana_api.py create-section <project_gid> --name "Ready"
python3 scripts/asana_api.py add-task-followers <task_gid> me
python3 scripts/asana_api.py add-task-tag <task_gid> <tag_gid>
python3 scripts/asana_api.py add-task-dependencies <task_gid> <other_task_gid>
python3 scripts/asana_api.py batch --actions '[{"method":"get","relative_path":"/users/me"}]'
```

## Guardrails

- Never print the PAT in output.
- Keep file uploads and external URL attachments explicit; do not guess attachment URLs.
- When changing membership-like relationships such as followers, tags, dependencies, or project membership, prefer the dedicated endpoints over full-object replacement.
- When using the generic `request` subcommand, remember that JSON bodies are wrapped in `{"data": ...}` by default unless `--no-wrap-data` is passed.
- Use `completed` as the canonical completion flag. Treat column/section names as additional context to report, not as an automatic status mapping.
- For project pull lists, do not present the raw assigned-task response as the final answer. Interpret the enriched context and tell the user which tasks are already done, which are true code work, and which should be closed or re-scoped first.

## References

- Core API guide: `references/api-overview.md`
- Common command cookbook: `references/recipes.md`
