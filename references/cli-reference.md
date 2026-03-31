# Asana API CLI Reference

Generated from `scripts/asana_api.py` by `scripts/generate_cli_docs.py`. Do not edit manually.

- CLI: Local Asana API helper
- Commands: 53

## Command Index

| Command | Summary |
| --- | --- |
| `request` | Run a generic Asana API request |
| `whoami` | Show the authenticated user |
| `workspaces` | List workspaces for the authenticated user |
| `teams` | List teams in a workspace |
| `users` | List users in a workspace |
| `projects` | List projects for a team |
| `task` | Inspect one or more tasks |
| `story` | Inspect one or more stories/comments by gid |
| `task-bundle` | Fetch one or more tasks with comments, attachments, and optional project workflow context |
| `task-status` | Summarize completion and board-column status for one or more tasks |
| `project` | Inspect one or more projects |
| `board` | Return project sections in order with tasks in each section |
| `project-tasks` | List tasks in a project |
| `project-assigned-tasks` | List assigned work in a project, including matching subtasks with parent section context |
| `sections` | List sections in a project |
| `section` | Inspect one or more sections |
| `section-tasks` | List tasks in a section |
| `create-section` | Create a section in a project |
| `update-section` | Rename a section |
| `close-out-sections` | Relocate tasks out of section(s) and delete the section(s) once empty |
| `search-tasks` | Search tasks within a workspace |
| `inbox-cleanup` | Generate an AI-gated My Tasks cleanup snapshot or apply an AI-authored cleanup plan |
| `daily-briefing` | Generate an AI-gated daily briefing snapshot or render an AI-authored morning briefing plan |
| `create-task` | Create a task |
| `update-task` | Update a task |
| `comment-task` | Create a task story/comment |
| `update-story` | Update an existing story/comment |
| `task-stories` | List stories/comments on one or more tasks |
| `task-comments` | List only comment stories on one or more tasks, including text and html_text |
| `task-projects` | List projects one or more tasks belong to |
| `add-task-project` | Add or move a task within a project/section |
| `remove-task-project` | Remove a task from a project |
| `add-task-followers` | Add followers to a task |
| `remove-task-followers` | Remove followers from a task |
| `tags` | List tags in a workspace |
| `create-tag` | Create a tag |
| `workspace-custom-fields` | List custom fields in a workspace |
| `team-custom-fields` | List team custom field settings |
| `project-custom-fields` | List custom field settings on one or more projects |
| `task-custom-fields` | List custom fields on one or more tasks |
| `create-custom-field` | Create a workspace custom field |
| `task-tags` | List tags on one or more tasks |
| `add-task-tag` | Add a tag to a task |
| `remove-task-tag` | Remove a tag from a task |
| `set-task-sorting-tag` | Set exactly one sorting tag on a task while preserving unrelated tags |
| `add-task-dependencies` | Add dependencies to a task |
| `remove-task-dependencies` | Remove dependencies from a task |
| `batch` | Run an Asana batch request from a JSON array of actions |
| `create-project` | Create a project |
| `update-project` | Update a project |
| `show-context` | Print local workspace/team defaults |
| `show-cache` | Print the local Asana entity cache |
| `trigger-rule` | Trigger an existing Asana rule that has a 'web request received' trigger |

## Shared Options

These options are available on every subcommand.

| Option | Kind | Description | Choices |
| --- | --- | --- | --- |
| `--compact` | flag | Print compact JSON |  |

## `request`

- Summary: Run a generic Asana API request
- Usage: `usage: asana_api.py request [-h] [--query QUERY] [--opt-fields OPT_FIELDS] [--opt-expand OPT_EXPAND] [--data DATA] [--data-file DATA_FILE] [--no-wrap-data] [--form FORM] [--file FILE] [--paginate] [--limit-pages LIMIT_PAGES] [--compact] method path`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `method` | yes | HTTP method, e.g. GET/POST/PUT/DELETE |
| `path` | yes | Relative /path or full URL |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--query` `QUERY` | option | no | Query param as key=value |  |
| `--opt-fields` `OPT_FIELDS` | option | no | Asana opt_fields value |  |
| `--opt-expand` `OPT_EXPAND` | option | no | Asana opt_expand value |  |
| `--data` `DATA` | option | no | JSON payload string |  |
| `--data-file` `DATA_FILE` | option | no | Path to JSON payload file |  |
| `--no-wrap-data` | flag | no | Do not auto-wrap JSON payloads in {"data": ...} |  |
| `--form` `FORM` | option | no | Multipart form field as key=value |  |
| `--file` `FILE` | option | no | Multipart file field as field=/abs/path |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `whoami`

- Summary: Show the authenticated user
- Usage: `usage: asana_api.py whoami [-h] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

No command-specific options.

## `workspaces`

- Summary: List workspaces for the authenticated user
- Usage: `usage: asana_api.py workspaces [-h] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

No command-specific options.

## `teams`

- Summary: List teams in a workspace
- Usage: `usage: asana_api.py teams [-h] [--workspace WORKSPACE] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |

## `users`

- Summary: List users in a workspace
- Usage: `usage: asana_api.py users [-h] [--workspace WORKSPACE] [--opt-fields OPT_FIELDS] [--paginate] [--limit-pages LIMIT_PAGES] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--opt-fields` `OPT_FIELDS` | option | no | Override result fields |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `projects`

- Summary: List projects for a team
- Usage: `usage: asana_api.py projects [-h] [--team TEAM] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--team` `TEAM` | option | no | Team GID or exact team name from asana-context.json |  |

## `task`

- Summary: Inspect one or more tasks
- Usage: `usage: asana_api.py task [-h] [--opt-fields OPT_FIELDS] [--compact] task_gids [task_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gids...` | yes | Task gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override task fields |  |

## `story`

- Summary: Inspect one or more stories/comments by gid
- Usage: `usage: asana_api.py story [-h] [--opt-fields OPT_FIELDS] [--compact] story_gids [story_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `story_gids...` | yes | Story gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override story fields |  |

## `task-bundle`

- Summary: Fetch one or more tasks with comments, attachments, and optional project workflow context
- Usage: `usage: asana_api.py task-bundle [-h] [--project-gid PROJECT_GID] [--task-opt-fields TASK_OPT_FIELDS] [--story-opt-fields STORY_OPT_FIELDS] [--attachment-opt-fields ATTACHMENT_OPT_FIELDS] [--compact] task_gids [task_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gids...` | yes | Task gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--project-gid` `PROJECT_GID` | option | no | Project GID to include section order and project custom field settings |  |
| `--task-opt-fields` `TASK_OPT_FIELDS` | option | no | Override task fields |  |
| `--story-opt-fields` `STORY_OPT_FIELDS` | option | no | Override story fields |  |
| `--attachment-opt-fields` `ATTACHMENT_OPT_FIELDS` | option | no | Override attachment fields |  |

## `task-status`

- Summary: Summarize completion and board-column status for one or more tasks
- Usage: `usage: asana_api.py task-status [-h] [--project PROJECT] [--opt-fields OPT_FIELDS] [--include-task-position] [--compact] task_gids [task_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gids...` | yes | Task gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--project` `PROJECT` | option | no | Limit membership analysis to one project GID |  |
| `--opt-fields` `OPT_FIELDS` | option | no | Override task fields |  |
| `--include-task-position` | flag | no | Also look up the task's position inside its current section |  |

## `project`

- Summary: Inspect one or more projects
- Usage: `usage: asana_api.py project [-h] [--opt-fields OPT_FIELDS] [--compact] project_gids [project_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `project_gids...` | yes | Project gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override project fields |  |

## `board`

- Summary: Return project sections in order with tasks in each section
- Usage: `usage: asana_api.py board [-h] [--opt-fields OPT_FIELDS] [--context] [--compact] project_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `project_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override per-task fields in board output |  |
| `--context` | flag | no | Include workflow context stats (field coverage, staleness, assignee distribution) |  |

## `project-tasks`

- Summary: List tasks in a project
- Usage: `usage: asana_api.py project-tasks [-h] [--opt-fields OPT_FIELDS] [--paginate] [--limit-pages LIMIT_PAGES] [--compact] project_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `project_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override task fields |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `project-assigned-tasks`

- Summary: List assigned work in a project, including matching subtasks with parent section context
- Usage: `usage: asana_api.py project-assigned-tasks [-h] [--workspace WORKSPACE] [--assignee ASSIGNEE] [--completed COMPLETED] [--opt-fields OPT_FIELDS] [--include-task-position] [--include-comments] [--comment-limit COMMENT_LIMIT] [--include-attachments] [--paginate] [--limit-pages LIMIT_PAGES] [--compact] project_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `project_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--assignee` `ASSIGNEE` | option | no | Assignee filter, defaults to the current user from asana-context.json; accepts gid, exact cached name, or exact cached email |  |
| `--completed` `COMPLETED` | option | no | Filter by completion |  |
| `--opt-fields` `OPT_FIELDS` | option | no | Override result fields |  |
| `--include-task-position` | flag | no | Also look up each task's position inside its effective board section |  |
| `--include-comments` | flag | no | Include recent comment context for each task |  |
| `--comment-limit` `COMMENT_LIMIT` | option | no | Maximum number of recent comments to keep per task when --include-comments is set |  |
| `--include-attachments` | flag | no | Include task attachments and derived image URLs for each task |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `sections`

- Summary: List sections in a project
- Usage: `usage: asana_api.py sections [-h] [--opt-fields OPT_FIELDS] [--compact] project_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `project_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override section fields |  |

## `section`

- Summary: Inspect one or more sections
- Usage: `usage: asana_api.py section [-h] [--opt-fields OPT_FIELDS] [--compact] section_gids [section_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `section_gids...` | yes | Section gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override section fields |  |

## `section-tasks`

- Summary: List tasks in a section
- Usage: `usage: asana_api.py section-tasks [-h] [--opt-fields OPT_FIELDS] [--paginate] [--limit-pages LIMIT_PAGES] [--compact] section_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `section_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override task fields |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `create-section`

- Summary: Create a section in a project
- Usage: `usage: asana_api.py create-section [-h] --name NAME [--compact] project_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `project_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--name` `NAME` | option | yes |  |  |

## `update-section`

- Summary: Rename a section
- Usage: `usage: asana_api.py update-section [-h] --name NAME [--compact] section_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `section_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--name` `NAME` | option | yes |  |  |

## `close-out-sections`

- Summary: Relocate tasks out of section(s) and delete the section(s) once empty
- Usage: `usage: asana_api.py close-out-sections [-h] --section SECTION [--move-to MOVE_TO] [--completed-mode {all,completed,incomplete}] [--limit-pages LIMIT_PAGES] [--apply] [--compact] project_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `project_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--section` `SECTION` | option | yes | Source section gid or exact name; pass multiple times for multiple sections |  |
| `--move-to` `MOVE_TO` | option | no | Destination section gid or exact name within the same project |  |
| `--completed-mode` `COMPLETED_MODE` | option | no | Which tasks to relocate before attempting deletion | `all`, `completed`, `incomplete` |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop section task pagination after N pages while collecting tasks |  |
| `--apply` | flag | no | Move selected tasks and delete sections that end up empty |  |

## `search-tasks`

- Summary: Search tasks within a workspace
- Usage: `usage: asana_api.py search-tasks [-h] --text TEXT [--workspace WORKSPACE] [--project PROJECT] [--assignee ASSIGNEE] [--completed COMPLETED] [--opt-fields OPT_FIELDS] [--paginate] [--limit-pages LIMIT_PAGES] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--text` `TEXT` | option | yes | Search text |  |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--project` `PROJECT` | option | no | Project GID filter |  |
| `--assignee` `ASSIGNEE` | option | no | Assignee filter, e.g. me, user gid, exact cached user name, or exact cached email |  |
| `--completed` `COMPLETED` | option | no | Filter by completion |  |
| `--opt-fields` `OPT_FIELDS` | option | no | Override result fields |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `inbox-cleanup`

- Summary: Generate an AI-gated My Tasks cleanup snapshot or apply an AI-authored cleanup plan
- Usage: `usage: asana_api.py inbox-cleanup [-h] [--workspace WORKSPACE] [--source-section SOURCE_SECTION] [--all-open] [--snapshot-file SNAPSHOT_FILE] [--plan-template-file PLAN_TEMPLATE_FILE] [--plan-file PLAN_FILE] [--apply] [--include-low-confidence] [--max-tasks MAX_TASKS] [--no-paginate] [--limit-pages LIMIT_PAGES] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--source-section` `SOURCE_SECTION` | option | no | My Tasks section name to triage from; defaults to Recently assigned |  |
| `--all-open` | flag | no | Ignore source-section filtering and include all open tasks in My Tasks |  |
| `--snapshot-file` `SNAPSHOT_FILE` | option | no | Write the AI-gating snapshot JSON to this file in addition to stdout |  |
| `--plan-template-file` `PLAN_TEMPLATE_FILE` | option | no | Write an editable cleanup plan template JSON to this file |  |
| `--plan-file` `PLAN_FILE` | option | no | Path to an AI-authored cleanup plan JSON to preview or apply |  |
| `--apply` | flag | no | Apply the provided AI-authored plan file by moving tasks into the requested sections |  |
| `--include-low-confidence` | flag | no | When applying a plan, also move tasks marked low confidence instead of leaving them for user review |  |
| `--max-tasks` `MAX_TASKS` | option | no | Limit how many filtered tasks to process after section filtering |  |
| `--no-paginate` | flag | no | Do not follow My Tasks next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop My Tasks pagination after N pages |  |

## `daily-briefing`

- Summary: Generate an AI-gated daily briefing snapshot or render an AI-authored morning briefing plan
- Usage: `usage: asana_api.py daily-briefing [-h] [--workspace WORKSPACE] [--max-tasks MAX_TASKS] [--no-paginate] [--limit-pages LIMIT_PAGES] [--snapshot-file SNAPSHOT_FILE] [--plan-template-file PLAN_TEMPLATE_FILE] [--plan-file PLAN_FILE] [--markdown] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--max-tasks` `MAX_TASKS` | option | no | Limit how many My Tasks items to include in the briefing snapshot |  |
| `--no-paginate` | flag | no | Do not follow My Tasks next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop My Tasks pagination after N pages |  |
| `--snapshot-file` `SNAPSHOT_FILE` | option | no | Write the daily briefing snapshot JSON to this file in addition to stdout |  |
| `--plan-template-file` `PLAN_TEMPLATE_FILE` | option | no | Write an editable daily briefing plan template JSON to this file |  |
| `--plan-file` `PLAN_FILE` | option | no | Path to an AI-authored daily briefing plan JSON to render |  |
| `--markdown` | flag | no | Print the rendered markdown briefing from the provided AI-authored plan instead of JSON |  |

## `create-task`

- Summary: Create a task
- Usage: `usage: asana_api.py create-task [-h] --name NAME [--workspace WORKSPACE] [--project PROJECT] [--parent PARENT] [--assignee ASSIGNEE] [--notes NOTES] [--html-notes HTML_NOTES] [--due-on DUE_ON] [--due-at DUE_AT] [--custom-field CUSTOM_FIELD] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--name` `NAME` | option | yes |  |  |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--project` `PROJECT` | option | no | Project GID |  |
| `--parent` `PARENT` | option | no | Parent task GID |  |
| `--assignee` `ASSIGNEE` | option | no | Assignee gid, me, exact cached user name, or exact cached email |  |
| `--notes` `NOTES` | option | no |  |  |
| `--html-notes` `HTML_NOTES` | option | no |  |  |
| `--due-on` `DUE_ON` | option | no |  |  |
| `--due-at` `DUE_AT` | option | no |  |  |
| `--custom-field` `CUSTOM_FIELD` | option | no | Custom field as gid=value |  |

## `update-task`

- Summary: Update a task
- Usage: `usage: asana_api.py update-task [-h] [--name NAME] [--assignee ASSIGNEE] [--notes NOTES] [--html-notes HTML_NOTES] [--due-on DUE_ON] [--due-at DUE_AT] [--completed COMPLETED] [--custom-field CUSTOM_FIELD] [--compact] task_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--name` `NAME` | option | no |  |  |
| `--assignee` `ASSIGNEE` | option | no | Assignee gid, me, exact cached user name, or exact cached email |  |
| `--notes` `NOTES` | option | no |  |  |
| `--html-notes` `HTML_NOTES` | option | no |  |  |
| `--due-on` `DUE_ON` | option | no |  |  |
| `--due-at` `DUE_AT` | option | no |  |  |
| `--completed` `COMPLETED` | option | no |  |  |
| `--custom-field` `CUSTOM_FIELD` | option | no | Custom field as gid=value |  |

## `comment-task`

- Summary: Create a task story/comment
- Usage: `usage: asana_api.py comment-task [-h] [--text TEXT] [--text-file TEXT_FILE] [--html-text HTML_TEXT] [--html-text-file HTML_TEXT_FILE] [--compact] task_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--text` `TEXT` | option | no | Plain-text comment body |  |
| `--text-file` `TEXT_FILE` | option | no | Read plain-text comment body from file |  |
| `--html-text` `HTML_TEXT` | option | no | Rich-text HTML comment body |  |
| `--html-text-file` `HTML_TEXT_FILE` | option | no | Read rich-text HTML comment body from file |  |

## `update-story`

- Summary: Update an existing story/comment
- Usage: `usage: asana_api.py update-story [-h] [--text TEXT] [--text-file TEXT_FILE] [--html-text HTML_TEXT] [--html-text-file HTML_TEXT_FILE] [--compact] story_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `story_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--text` `TEXT` | option | no | Plain-text comment body |  |
| `--text-file` `TEXT_FILE` | option | no | Read plain-text comment body from file |  |
| `--html-text` `HTML_TEXT` | option | no | Rich-text HTML comment body |  |
| `--html-text-file` `HTML_TEXT_FILE` | option | no | Read rich-text HTML comment body from file |  |

## `task-stories`

- Summary: List stories/comments on one or more tasks
- Usage: `usage: asana_api.py task-stories [-h] [--opt-fields OPT_FIELDS] [--paginate] [--limit-pages LIMIT_PAGES] [--compact] task_gids [task_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gids...` | yes | Task gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override story fields |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `task-comments`

- Summary: List only comment stories on one or more tasks, including text and html_text
- Usage: `usage: asana_api.py task-comments [-h] [--opt-fields OPT_FIELDS] [--paginate] [--limit-pages LIMIT_PAGES] [--compact] task_gids [task_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gids...` | yes | Task gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override story fields |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `task-projects`

- Summary: List projects one or more tasks belong to
- Usage: `usage: asana_api.py task-projects [-h] [--opt-fields OPT_FIELDS] [--compact] task_gids [task_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gids...` | yes | Task gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override project fields |  |

## `add-task-project`

- Summary: Add or move a task within a project/section
- Usage: `usage: asana_api.py add-task-project [-h] [--section SECTION] [--insert-before INSERT_BEFORE] [--insert-after INSERT_AFTER] [--compact] task_gid project_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |
| `project_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--section` `SECTION` | option | no | Section GID for placement |  |
| `--insert-before` `INSERT_BEFORE` | option | no | Anchor task GID or literal null |  |
| `--insert-after` `INSERT_AFTER` | option | no | Anchor task GID or literal null |  |

## `remove-task-project`

- Summary: Remove a task from a project
- Usage: `usage: asana_api.py remove-task-project [-h] [--compact] task_gid project_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |
| `project_gid` | yes |  |

### Command Options

No command-specific options.

## `add-task-followers`

- Summary: Add followers to a task
- Usage: `usage: asana_api.py add-task-followers [-h] [--compact] task_gid followers [followers ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |
| `followers...` | yes | Follower gids, me, exact cached user names/emails; comma-separated values allowed |

### Command Options

No command-specific options.

## `remove-task-followers`

- Summary: Remove followers from a task
- Usage: `usage: asana_api.py remove-task-followers [-h] [--compact] task_gid followers [followers ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |
| `followers...` | yes | Follower gids, me, exact cached user names/emails; comma-separated values allowed |

### Command Options

No command-specific options.

## `tags`

- Summary: List tags in a workspace
- Usage: `usage: asana_api.py tags [-h] [--workspace WORKSPACE] [--opt-fields OPT_FIELDS] [--paginate] [--limit-pages LIMIT_PAGES] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--opt-fields` `OPT_FIELDS` | option | no | Override tag fields |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `create-tag`

- Summary: Create a tag
- Usage: `usage: asana_api.py create-tag [-h] --name NAME [--workspace WORKSPACE] [--color COLOR] [--notes NOTES] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--name` `NAME` | option | yes |  |  |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--color` `COLOR` | option | no | Tag color |  |
| `--notes` `NOTES` | option | no |  |  |

## `workspace-custom-fields`

- Summary: List custom fields in a workspace
- Usage: `usage: asana_api.py workspace-custom-fields [-h] [--workspace WORKSPACE] [--opt-fields OPT_FIELDS] [--paginate] [--limit-pages LIMIT_PAGES] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--opt-fields` `OPT_FIELDS` | option | no | Override field list |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `team-custom-fields`

- Summary: List team custom field settings
- Usage: `usage: asana_api.py team-custom-fields [-h] [--team TEAM] [--opt-fields OPT_FIELDS] [--paginate] [--limit-pages LIMIT_PAGES] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--team` `TEAM` | option | no | Team GID or exact team name from asana-context.json |  |
| `--opt-fields` `OPT_FIELDS` | option | no | Override field list |  |
| `--paginate` | flag | no | Follow Asana next_page links |  |
| `--limit-pages` `LIMIT_PAGES` | option | no | Stop pagination after N pages |  |

## `project-custom-fields`

- Summary: List custom field settings on one or more projects
- Usage: `usage: asana_api.py project-custom-fields [-h] [--opt-fields OPT_FIELDS] [--compact] project_gids [project_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `project_gids...` | yes | Project gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override field list |  |

## `task-custom-fields`

- Summary: List custom fields on one or more tasks
- Usage: `usage: asana_api.py task-custom-fields [-h] [--opt-fields OPT_FIELDS] [--compact] task_gids [task_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gids...` | yes | Task gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override field list |  |

## `create-custom-field`

- Summary: Create a workspace custom field
- Usage: `usage: asana_api.py create-custom-field [-h] --name NAME [--workspace WORKSPACE] --resource-subtype RESOURCE_SUBTYPE [--description DESCRIPTION] [--precision PRECISION] [--enum-option ENUM_OPTION] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--name` `NAME` | option | yes |  |  |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--resource-subtype` `RESOURCE_SUBTYPE` | option | yes | Asana custom field subtype, e.g. text, number, enum, multi_enum |  |
| `--description` `DESCRIPTION` | option | no |  |  |
| `--precision` `PRECISION` | option | no |  |  |
| `--enum-option` `ENUM_OPTION` | option | no | Enum option name; repeat for multiple values |  |

## `task-tags`

- Summary: List tags on one or more tasks
- Usage: `usage: asana_api.py task-tags [-h] [--opt-fields OPT_FIELDS] [--compact] task_gids [task_gids ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gids...` | yes | Task gids; comma-separated values allowed |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--opt-fields` `OPT_FIELDS` | option | no | Override tag fields |  |

## `add-task-tag`

- Summary: Add a tag to a task
- Usage: `usage: asana_api.py add-task-tag [-h] [--workspace WORKSPACE] [--compact] task_gid tag_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |
| `tag_gid` | yes | Tag gid or exact tag name |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override for tag-name resolution |  |

## `remove-task-tag`

- Summary: Remove a tag from a task
- Usage: `usage: asana_api.py remove-task-tag [-h] [--workspace WORKSPACE] [--compact] task_gid tag_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |
| `tag_gid` | yes | Tag gid or exact tag name |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override for tag-name resolution |  |

## `set-task-sorting-tag`

- Summary: Set exactly one sorting tag on a task while preserving unrelated tags
- Usage: `usage: asana_api.py set-task-sorting-tag [-h] [--workspace WORKSPACE] [--sorting-label SORTING_LABEL] [--compact] task_gid sorting_tag`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |
| `sorting_tag` | yes | Desired sorting tag gid or exact tag name |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override for tag-name resolution |  |
| `--sorting-label` `SORTING_LABEL` | option | no | Allowed sorting tag name; repeat to override the default sorter set |  |

## `add-task-dependencies`

- Summary: Add dependencies to a task
- Usage: `usage: asana_api.py add-task-dependencies [-h] [--compact] task_gid dependencies [dependencies ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |
| `dependencies...` | yes | Dependency task gids; comma-separated values allowed |

### Command Options

No command-specific options.

## `remove-task-dependencies`

- Summary: Remove dependencies from a task
- Usage: `usage: asana_api.py remove-task-dependencies [-h] [--compact] task_gid dependencies [dependencies ...]`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `task_gid` | yes |  |
| `dependencies...` | yes | Dependency task gids; comma-separated values allowed |

### Command Options

No command-specific options.

## `batch`

- Summary: Run an Asana batch request from a JSON array of actions
- Usage: `usage: asana_api.py batch [-h] [--actions ACTIONS] [--actions-file ACTIONS_FILE] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--actions` `ACTIONS` | option | no | Inline JSON array of batch actions |  |
| `--actions-file` `ACTIONS_FILE` | option | no | Path to a JSON file containing a batch actions array |  |

## `create-project`

- Summary: Create a project
- Usage: `usage: asana_api.py create-project [-h] --name NAME [--team TEAM] [--workspace WORKSPACE] [--notes NOTES] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--name` `NAME` | option | yes |  |  |
| `--team` `TEAM` | option | no | Team GID or exact team name from asana-context.json |  |
| `--workspace` `WORKSPACE` | option | no | Workspace GID override |  |
| `--notes` `NOTES` | option | no |  |  |

## `update-project`

- Summary: Update a project
- Usage: `usage: asana_api.py update-project [-h] [--name NAME] [--notes NOTES] [--archived ARCHIVED] [--compact] project_gid`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `project_gid` | yes |  |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--name` `NAME` | option | no |  |  |
| `--notes` `NOTES` | option | no |  |  |
| `--archived` `ARCHIVED` | option | no |  |  |

## `show-context`

- Summary: Print local workspace/team defaults
- Usage: `usage: asana_api.py show-context [-h] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

No command-specific options.

## `show-cache`

- Summary: Print the local Asana entity cache
- Usage: `usage: asana_api.py show-cache [-h] [--compact]`
- Shared options: see [Shared Options](#shared-options)

### Command Options

No command-specific options.

## `trigger-rule`

- Summary: Trigger an existing Asana rule that has a 'web request received' trigger
- Usage: `usage: asana_api.py trigger-rule [-h] --task TASK_GID [--action-data KEY=VALUE] [--compact] trigger_identifier`
- Shared options: see [Shared Options](#shared-options)

### Positional Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `trigger_identifier` | yes | Trigger identifier from the Asana rule's incoming web request URL |

### Command Options

| Option | Kind | Required | Description | Choices |
| --- | --- | --- | --- | --- |
| `--task` `TASK_GID` | option | yes | Task GID where rule actions will be performed |  |
| `--action-data` `KEY=VALUE` | option | no | Custom key=value data available as dynamic variables in rule actions (repeatable) |  |
