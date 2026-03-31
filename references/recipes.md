# Asana Recipes

## Contents

- Read operations
- Write operations
- Relationship operations
- Attachments and advanced requests
- Workflow analysis and rule triggers

All commands below use:

`python3 scripts/asana_api.py`

## Read operations

Identify the current user and workspaces:

```bash
python3 scripts/asana_api.py whoami
python3 scripts/asana_api.py workspaces
python3 scripts/asana_api.py workspace-custom-fields
python3 scripts/asana_api.py show-cache
```

These commands also refresh the local cache at `~/.agent-skills/asana/asana-cache.json`, which stores discovered workspaces, teams, projects, users, and tags for later resolution.
Discovery-style commands such as `whoami`, `workspaces`, `teams`, `users`, `show-context`, `show-cache`, and `inbox-cleanup` may also include a `skill_advertising` block in the JSON output. On first run, it highlights the best commands for the workspace and uses My Tasks size to recommend whether `inbox-cleanup` should be the next step.

List teams in the default workspace:

```bash
python3 scripts/asana_api.py teams
python3 scripts/asana_api.py users
python3 scripts/asana_api.py tags
```

List projects for a team:

```bash
python3 scripts/asana_api.py projects --team <team_gid>
python3 scripts/asana_api.py projects --team "Marketing & Communications"
```

Inspect a task or project:

```bash
python3 scripts/asana_api.py task <task_gid>
python3 scripts/asana_api.py task <task_gid> <task_gid>
python3 scripts/asana_api.py story <story_gid>
python3 scripts/asana_api.py task-status <task_gid> <task_gid>
python3 scripts/asana_api.py task-bundle <task_gid> --project-gid <project_gid>
python3 scripts/asana_api.py task-status <task_gid> --include-task-position
python3 scripts/asana_api.py project <project_gid>
python3 scripts/asana_api.py task-projects <task_gid>
python3 scripts/asana_api.py task-stories <task_gid>
python3 scripts/asana_api.py task-comments <task_gid>
python3 scripts/asana_api.py task-custom-fields <task_gid>
```

`task-bundle` is the best default for planning work from one ticket.
It returns the task body, filtered comments, attachments, image URLs, project custom-field settings, and project section order together.

These lookup-style read commands now accept one or many gids directly.
Pass gids as separate arguments or as comma-separated values and expect the same wrapper shape every time:

```json
{
  "command": "task-status",
  "count": 2,
  "items": [
    {"requested_gid": "123", "status_code": 200, "result": {...}},
    {"requested_gid": "456", "status_code": 200, "result": {...}}
  ]
}
```

Use `story` when you already have a story/comment gid and want the direct permalink plus parent task link without paying for a broader task lookup.

List tasks or sections inside a project:

```bash
python3 scripts/asana_api.py project-tasks <project_gid> --paginate
python3 scripts/asana_api.py project-assigned-tasks <project_gid> --completed false
python3 scripts/asana_api.py project-assigned-tasks <project_gid> --completed false --include-task-position --include-comments --comment-limit 3 --include-attachments
python3 scripts/asana_api.py sections <project_gid>
python3 scripts/asana_api.py section-tasks <section_gid>
python3 scripts/asana_api.py board <project_gid>
python3 scripts/asana_api.py project-custom-fields <project_gid>
python3 scripts/asana_api.py team-custom-fields --team "Marketing & Communications"
```

Use `project-assigned-tasks` when the question is "what is assigned to me in this project?" because it includes matching subtasks and adds parent task section context for subtasks that do not carry direct project memberships.
Use the contextual flags when the question is "what should I actually work on now?" so the response includes section order, task position, recent comments, and attachments instead of only a raw checklist.
Use `project-tasks` when you truly want the board's project task list itself.

Use `board` and `task-status` together when the model needs to reason about workflow state.
These commands return the exact section names and section ordering from Asana, plus `completed` on the task.
They do not infer whether a section means “done”.

Recommended triage flow for AI-generated pull docs:

Use a two-pass workflow: gather enriched assigned-task context first, split the work into implementation buckets, then run `task-bundle` only for the short list that still looks like real coding work.

Full spec:

- `references/automations/project-assigned-working-set.md`

Search tasks in a workspace:

```bash
python3 scripts/asana_api.py search-tasks --text "homepage" --project <project_gid>
python3 scripts/asana_api.py search-tasks --text "homepage" --project <project_gid> --assignee "Exact User Name"
```

After `users` has been run at least once, commands that accept assignees or followers can resolve exact cached user names or emails in addition to raw gids and `me`.

For long reusable automations, keep this cookbook concise and put the full body in `references/automations/`.
The recipe entries below are discovery summaries; when a matching automation spec exists, open the full `.md` file before implementing or scheduling the automation.

Build a manager-facing weekly summary for one employee:

Use this when the question is "what has this person been working on?" and the desired output is a manager-readable summary task or note rather than raw task JSON.

Use a search-and-summarize workflow over board-only views, bucket work into `Completed`, `In Progress`, and `Blocked / Stalled`, then create one manager-facing summary artifact with direct task links and recommended follow-up messages.

Full spec:

- `references/automations/weekly-manager-summary.md`

Build a recurring follow-up summary for tasks I am involved in but do not own:

Use this when the question is "what open tasks assigned to other people may still need something from me?" and the desired output is one recurring summary task in My Tasks instead of a raw search result dump.

This recipe works well as a scheduled Codex automation or Claude schedule, especially for a weekly Friday-morning check-in.

Use an involvement-scan workflow, classify each task into `Needs my action` or `FYI / watching`, create or update one summary task for the run date, and keep LLM usage constrained to ambiguous comment threads only.

Full spec:

- `references/automations/friday-follow-up-summary.md`

Clean up My Tasks intake into review buckets:

```bash
python3 scripts/asana_api.py inbox-cleanup
python3 scripts/asana_api.py inbox-cleanup --snapshot-file /tmp/asana-inbox-snapshot.json --plan-template-file /tmp/asana-inbox-plan.json
python3 scripts/asana_api.py inbox-cleanup --all-open --max-tasks 50
python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json
python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json --apply
python3 scripts/asana_api.py inbox-cleanup --plan-file /tmp/asana-inbox-plan.json --apply --include-low-confidence
```

Use `inbox-cleanup` when the question is "clean up my My Tasks intake and let AI decide the categories and buckets".
Treat it as an AI-gated workflow rather than a filing pass: the first run emits a snapshot plus plan scaffold, the AI defines the categories and per-task decisions in JSON, and only the approved plan is previewed or applied. Ambiguous tasks should stay interactive with `ask_user` questions instead of being auto-bucketed by Python.

Full spec:

- `references/automations/inbox-cleanup.md`

Build a full morning command center for My Tasks:

```bash
python3 scripts/asana_api.py daily-briefing
python3 scripts/asana_api.py daily-briefing --snapshot-file /tmp/asana-daily-briefing-snapshot.json --plan-template-file /tmp/asana-daily-briefing-plan.json
python3 scripts/asana_api.py daily-briefing --max-tasks 50
python3 scripts/asana_api.py daily-briefing --plan-file /tmp/asana-daily-briefing-plan.json
python3 scripts/asana_api.py daily-briefing --plan-file /tmp/asana-daily-briefing-plan.json --markdown
```

Use `daily-briefing` when the question is "what should I focus on this morning?" or "give me the full command center for my tasks."
It is intentionally read-only and now AI-gated: the helper emits a snapshot plus plan scaffold, but the agent should author that plan itself, render the final command center, and only ask the user about the small set of genuinely ambiguous tasks. Do not rely on built-in heuristics to decide the morning queue.

Full spec:

- `references/automations/daily-briefing.md`

Close out stale personal sections by relocating tasks, then deleting the empty section:

```bash
python3 scripts/asana_api.py close-out-sections <project_gid> \
  --section "Old Section" \
  --move-to "Work Completed" \
  --completed-mode completed

python3 scripts/asana_api.py close-out-sections <project_gid> \
  --section "Old Section" \
  --section "Another Old Section" \
  --move-to "Backlog" \
  --completed-mode all \
  --apply
```

Use `close-out-sections` when the question is "move everything out of these stale sections and remove them."
It should behave like a safety-first cleanup tool: preview first, move the requested task set, verify emptiness, then delete only when safe.

Full spec:

- `references/automations/close-out-sections.md`

## Write operations

Create a task in a project:

```bash
python3 scripts/asana_api.py create-task \
  --name "Draft Q2 launch summary" \
  --project <project_gid> \
  --assignee me \
  --due-on 2026-03-31 \
  --custom-field <custom_field_gid>="In progress"
```

Create a task directly in the default workspace:

```bash
python3 scripts/asana_api.py create-task \
  --name "Inbox triage" \
  --workspace <workspace_gid>
```

Update task fields:

```bash
python3 scripts/asana_api.py update-task <task_gid> \
  --name "Updated title" \
  --completed true \
  --due-on 2026-03-25
```

Comment on a task:

```bash
python3 scripts/asana_api.py comment-task <task_gid> \
  --text "Posted from the AI assistant after verifying the latest status."
```

Successful write responses now include:

- `review_url`: direct Asana link to the created or updated object
- `target_review_url`: for story/comment writes, the parent task link when Asana returns it

Comment on a task with proper Asana rich-text formatting:

```bash
python3 scripts/asana_api.py comment-task <task_gid> \
  --html-text-file /absolute/path/to/comment.html
```

Update an existing comment/story with rich text:

```bash
python3 scripts/asana_api.py update-story <story_gid> \
  --html-text-file /absolute/path/to/comment.html
```

Recommended AI-authored comment template:

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

If an AI disclaimer message is passed as one long inline HTML blob or in the older single-list disclaimer shape, the helper will normalize it into a mixed block/list structure before posting, but the template above is still the preferred shape.

Create or update a project:

```bash
python3 scripts/asana_api.py create-project \
  --name "Website refresh" \
  --team <team_gid>

python3 scripts/asana_api.py update-project <project_gid> \
  --name "Website refresh v2"
```

Create a section in a project:

```bash
python3 scripts/asana_api.py create-section <project_gid> \
  --name "Ready for review"

python3 scripts/asana_api.py update-section <section_gid> \
  --name "In QA"
```

## Relationship operations

Add a task to a project:

```bash
python3 scripts/asana_api.py add-task-project <task_gid> <project_gid>
python3 scripts/asana_api.py remove-task-project <task_gid> <project_gid>
```

Add followers:

```bash
python3 scripts/asana_api.py add-task-followers <task_gid> me
python3 scripts/asana_api.py remove-task-followers <task_gid> me
```

Add a dependency:

```bash
python3 scripts/asana_api.py add-task-dependencies <task_gid> <other_task_gid>
python3 scripts/asana_api.py remove-task-dependencies <task_gid> <other_task_gid>
```

Tag a task:

```bash
python3 scripts/asana_api.py create-tag --name "Needs Copy"
python3 scripts/asana_api.py add-task-tag <task_gid> <tag_gid>
python3 scripts/asana_api.py remove-task-tag <task_gid> <tag_gid>
```

Create a custom field:

```bash
python3 scripts/asana_api.py create-custom-field \
  --name "Launch status" \
  --resource-subtype enum \
  --enum-option "Not started" \
  --enum-option "In progress" \
  --enum-option "Done"
```

## Attachments and advanced requests

Attach a local file to a task:

```bash
python3 scripts/asana_api.py request POST /tasks/<task_gid>/attachments \
  --file file=/absolute/path/to/file.pdf
```

Attach an external URL to a task:

```bash
python3 scripts/asana_api.py request POST /tasks/<task_gid>/attachments \
  --form resource_subtype=external \
  --form name="Spec doc" \
  --form url="https://example.com/spec"
```

Run a generic GET with field filtering:

```bash
python3 scripts/asana_api.py request GET /tasks/<task_gid> \
  --opt-fields gid,name,completed,assignee.name,memberships.section.name
```

Run a raw batch request without auto-wrapping the JSON body:

```bash
python3 scripts/asana_api.py request POST /batch \
  --no-wrap-data \
  --data '{"data":{"actions":[{"method":"get","relative_path":"/users/me"},{"method":"get","relative_path":"/users/me/workspaces"}]}}'
```

Run a batch request through the convenience wrapper:

```bash
python3 scripts/asana_api.py batch \
  --actions '[{"method":"get","relative_path":"/users/me"},{"method":"get","relative_path":"/projects/<project_gid>"}]'
```

## Workflow analysis and rule triggers

Get a board snapshot with workflow context stats (custom field coverage, staleness, assignee distribution):

```bash
python3 scripts/asana_api.py board <project_gid> --context
```

The `--context` flag enriches the standard board output with a `context` key containing:
- `project_summary`: total/completed/incomplete counts per section with percentages
- `custom_field_coverage`: which fields are filled and how consistently
- `date_coverage`: due date usage and overdue count
- `assignee_distribution`: who owns what, and how many tasks are unassigned
- `staleness`: how many tasks haven't been modified in 7/14/30+ days

Use this output together with `references/workflow-patterns.md` to recommend specific
Asana rules the user should create in the UI.

Trigger an existing Asana rule that has a "web request received" trigger:

```bash
python3 scripts/asana_api.py trigger-rule <trigger_identifier> --task <task_gid>
```

Trigger with custom action data (available as dynamic variables in the rule's actions):

```bash
python3 scripts/asana_api.py trigger-rule <trigger_identifier> \
  --task <task_gid> \
  --action-data status=approved \
  --action-data reviewer=jane
```

To find the trigger identifier: open the project in Asana, go to Customize > Rules,
create or edit a rule with an "Incoming web request" trigger, and copy the identifier
from the trigger URL shown in the rule configuration.
