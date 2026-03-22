# Asana Recipes

## Contents

- Read operations
- Write operations
- Relationship operations
- Attachments and advanced requests

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
python3 scripts/asana_api.py story <story_gid>
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

1. Run `project-assigned-tasks` with `--include-task-position --include-comments --comment-limit 3 --include-attachments`.
2. Split the result into:
   - implemented / QA only
   - active code-now
   - needs repro before code
   - backlog / workflow cleanup
3. Run `task-bundle` only for the small set of tasks in `active code-now`.
4. If you publish a markdown summary, clearly label the raw snapshot versus your contextual working interpretation.

Search tasks in a workspace:

```bash
python3 scripts/asana_api.py search-tasks --text "homepage" --project <project_gid>
python3 scripts/asana_api.py search-tasks --text "homepage" --project <project_gid> --assignee "Eli Bosley"
```

After `users` has been run at least once, commands that accept assignees or followers can resolve exact cached user names or emails in addition to raw gids and `me`.

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
  <ul>
    <li>This message was generated by AI to summarize implementation status and verification.</li>
    <li><strong>Status:</strong> Pushed to branch <code>branch-name</code>.</li>
    <li><strong>Fixed:</strong></li>
    <li>First concrete change.</li>
    <li>Second concrete change.</li>
    <li><strong>Verification:</strong></li>
    <li><code>pnpm --filter ...</code></li>
  </ul>
</body>
```

If an AI disclaimer message is passed as one long inline HTML blob, the helper will normalize it into a list-based structure before posting, but the template above is still the preferred shape.

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
