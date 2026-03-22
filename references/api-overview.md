# Asana API Overview

## Contents

- Authentication and defaults
- Request shape
- Pagination and field selection
- Common endpoint map
- Official docs

## Authentication and defaults

- Base URL: `https://app.asana.com/api/1.0`
- Auth header: `Authorization: Bearer <PAT>`
- The local helper reads the PAT from `ASANA_ACCESS_TOKEN`, then from `~/.agent-skills/asana/asana_pat`, then the legacy `~/.codex/skills-data/asana/asana_pat`, and finally from the legacy in-skill `.secrets/asana_pat` unless `ASANA_TOKEN_FILE` is set.
- Workspace and team defaults can be stored in `~/.agent-skills/asana/asana-context.json` unless `ASANA_CONTEXT_FILE` is set.
- The helper also maintains a local entity cache at `~/.agent-skills/asana/asana-cache.json` unless `ASANA_CACHE_FILE` is set. The cache stores workspaces, teams, projects, users, and tags discovered by common read commands so later commands can reuse gids without extra lookups.

## Request shape

Most Asana JSON writes expect a top-level `data` object.

Examples:

```json
{"data":{"name":"Ship homepage refresh","workspace":"<workspace_gid>"}}
```

```json
{"data":{"notes":"Updated from AI assistant","completed":true}}
```

The helper wraps JSON payloads in `data` automatically unless you pass `--no-wrap-data`.

## Pagination and field selection

- Use `opt_fields` to request only the fields you need.
- Use `opt_expand` when you need expanded nested records.
- List endpoints may return `next_page`; use `--paginate` in the helper to follow it.
- For broad task lookup, prefer `GET /workspaces/{workspace_gid}/tasks/search`.
- For "assigned work in a project" pulls, prefer workspace search with `projects.any=<project_gid>` and `assignee.any=<user_gid>` over `GET /projects/{project_gid}/tasks`, because search results include matching subtasks while project task lists are top-level only.
- Cached exact user names and emails can be resolved back to gids for helper commands that accept assignees or followers.

## Common endpoint map

### Identity and workspace

- `GET /users/me`
- `GET /users/me/workspaces`
- `GET /workspaces/{workspace_gid}/teams`
- `GET /workspaces/{workspace_gid}/users`
- `GET /workspaces/{workspace_gid}/tags`

### Tasks

- `GET /tasks/{task_gid}`
- `GET /tasks`
- `GET /projects/{project_gid}/tasks`
- `GET /sections/{section_gid}/tasks`
- `GET /workspaces/{workspace_gid}/tasks/search`
- `POST /tasks`
- `PUT /tasks/{task_gid}`
- `DELETE /tasks/{task_gid}`
- `GET /tasks/{task_gid}/projects`
- `POST /tasks/{task_gid}/stories`
- `PUT /stories/{story_gid}`
- `GET /tasks/{task_gid}/stories`
- `POST /tasks/{task_gid}/addProject`
- `POST /tasks/{task_gid}/removeProject`
- `POST /tasks/{task_gid}/addFollowers`
- `POST /tasks/{task_gid}/removeFollowers`
- `POST /tasks/{task_gid}/addDependencies`
- `POST /tasks/{task_gid}/removeDependencies`
- `POST /tasks/{task_gid}/addTag`
- `POST /tasks/{task_gid}/removeTag`
- `POST /tasks/{task_gid}/attachments`

### Projects and sections

- `GET /projects/{project_gid}`
- `GET /teams/{team_gid}/projects`
- `POST /projects`
- `PUT /projects/{project_gid}`
- `GET /projects/{project_gid}/sections`
- `POST /projects/{project_gid}/sections`
- `GET /sections/{section_gid}`
- `PUT /sections/{section_gid}`

### Teams, tags, and custom fields

- `GET /teams/{team_gid}`
- `GET /tasks/{task_gid}/tags`
- `GET /workspaces/{workspace_gid}/tags`
- `POST /tags`
- `GET /workspaces/{workspace_gid}/custom_fields`
- `POST /custom_fields`

### Batch

- `POST /batch`

Use batch when several independent reads or writes should happen together and ordering is not dependent on prior responses.

## Rich text guidance

- Task/task-project comments (`stories`) support rich text through `html_text`.
- Task descriptions/notes support rich text through `html_notes`.
- Prefer rich text for AI-authored messages so headings, paragraphs, and lists render correctly in Asana.
- If the message includes structured status details, do not rely on Markdown or literal newline escapes inside plain `text`.
- Use only Asana-supported rich-text tags in API writes. Safe default tags for status updates are:
  - `<body>`
  - `<strong>`
  - `<em>`
  - `<u>`
  - `<s>`
  - `<code>`
  - `<ol>`
  - `<ul>`
  - `<li>`
  - `<a>`
  - `<blockquote>`
  - `<pre>`
- Do not use heading tags such as `<h1>` or paragraph tags such as `<p>` in API-authored comments unless you have re-verified support.

## Official docs

These references were used to shape this skill:

- API features overview: [https://developers.asana.com/docs/api-features](https://developers.asana.com/docs/api-features)
- Postman collection and environment setup: [https://developers.asana.com/docs/postman-collection](https://developers.asana.com/docs/postman-collection)
- Create a task: [https://developers.asana.com/reference/createtask](https://developers.asana.com/reference/createtask)
- Create a story on a task: [https://developers.asana.com/reference/createstoryfortask](https://developers.asana.com/reference/createstoryfortask)
- Update a story: [https://developers.asana.com/reference/updatestory](https://developers.asana.com/reference/updatestory)
- Get multiple tasks: [https://developers.asana.com/reference/gettasks](https://developers.asana.com/reference/gettasks)
- Get a project: [https://developers.asana.com/reference/getproject](https://developers.asana.com/reference/getproject)
