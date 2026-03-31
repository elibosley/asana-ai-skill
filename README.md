# Asana Agent Skill

An AI skill that lets Codex, Claude Code, and similar agents manage your Asana tasks, projects, and workflows using plain English.

## Setup (5 minutes)

You need two things: an Asana token and a one-time install. Your AI tool handles almost everything.

### Step 1: Create your Asana token

1. Sign in to [Asana](https://app.asana.com/).
2. Click your **profile photo** (top right).
3. Click **Settings**.
4. Click the **Apps** tab.
5. Click **View developer console** (near the bottom).
6. Click **Personal access tokens** on the left, then **Create new token**.
7. Name it anything (e.g. "AI Skill"), accept the terms, and click **Create token**.
8. **Copy the token immediately** — it is only shown once. Paste it somewhere safe (a notes app, a text file, anywhere temporary).

### Step 2: Let your AI do the rest

Open **Codex** or **Claude Code** and paste this entire block:

```text
Set up the private `asana` skill for me from `elibosley/asana-ai-skill` with as little manual work as possible.

Requirements:
- Ask me first which agent I want this installed for: `Codex`, `Claude Code`, or `both`
- If `~/Code/asana-ai-skill` does not exist, clone the repo there. If it does exist, update it safely.
- Confirm `python3` is available and do not add any pip dependencies unless they are actually needed
- After I answer, run the matching bootstrap command:
  - Codex: `python3 ~/Code/asana-ai-skill/scripts/bootstrap_skill.py --agent codex`
  - Claude Code: `python3 ~/Code/asana-ai-skill/scripts/bootstrap_skill.py --agent claude`
  - Both: `python3 ~/Code/asana-ai-skill/scripts/bootstrap_skill.py --agent both`
- Keep secrets out of git
- Install only the agent target I chose
- Enable the built-in auto-update path
- Use `~/.agent-skills/asana/` for token and context storage
- If `~/.agent-skills/asana/asana_pat` is missing, walk me through signing into Asana and creating one:
  sign in to `https://app.asana.com/`, then go to profile photo -> `Settings` -> `Apps` -> `View developer console` -> `Personal access tokens` -> `Create new token`
- Explain that the token is shown once and should be saved immediately
- Save the token to `~/.agent-skills/asana/asana_pat` with safe file permissions
- After the token is in place, rerun the bootstrap script so it can auto-build `asana-context.json`
- Verify the install by running `python3 ~/Code/asana-ai-skill/scripts/asana_api.py whoami`
- Verify the updater by running `python3 ~/Code/asana-ai-skill/scripts/update_skill.py --force`
- Never print the token in output
```

The AI will ask you a couple questions (which agent to install for, and to paste your token). Answer them and you are done.

### Step 3: Verify it worked

After setup, ask your AI:

> Show me my Asana workspaces

If it returns your workspace name, everything is connected.

## Try It Out

Once installed, just talk to your AI in plain English. Here are some things you can do:

| Say this | What happens |
|---|---|
| "Give me a morning briefing of my tasks" | See everything due today, overdue, and coming up |
| "Show me all tasks assigned to me in [project name]" | Pull your tasks with context, comments, and attachments |
| "Import tasks from a spreadsheet into Asana" | Bulk-create tasks from a CSV with assignees, due dates, and sections |
| "Clean up my Asana inbox" | Classify tasks, suggest next actions, flag what needs attention |
| "Tag my My Tasks list as Quick Win / Deep Work / Waiting" | Review each task and normalize exactly one sorter tag while preserving project tags |
| "Close out stale sections in my tasks" | Safely archive old sections after moving remaining tasks |
| "Find tasks about [topic] in [project]" | Search across projects by keyword |
| "Create a task for [person] to [do something] by [date]" | Create and assign a task in one sentence |

If your agent exposes skill slash commands, the install also adds workflow-specific entrypoints:

- `/asana-daily-briefing`
- `/asana-inbox-cleanup`
- `/asana-close-out-sections`
- `/asana-project-working-set`
- `/asana-weekly-manager-summary`
- `/asana-friday-follow-up-summary`

## What Is Included

- **Daily briefing** — a read-only morning command center for My Tasks with direct links and priority buckets
- **Project task pulls** — fetch assigned tasks enriched with section order, position, recent comments, and attachments
- **Inbox cleanup** — classify tasks, suggest next actions, flag execution-ready work, and optionally draft AI comments
- **Sorting tag normalization** — keep exactly one personal sorter tag such as `Quick Win`, `Deep Work`, or `Needs Clarity` on a task without touching unrelated project tags
- **Section management** — retire stale personal sections safely by previewing, relocating tasks, and deleting only when empty
- **Bulk import** — create tasks from spreadsheets with assignees, due dates, priorities, and sections
- **Direct links** — every task the AI creates or modifies includes a clickable Asana URL
- **Workflow entrypoints** — install companion skills such as `/asana-daily-briefing` and `/asana-inbox-cleanup` that jump straight into the higher-level automation specs

## CLI Reference

The repo now ships a parser-derived CLI reference so agents and humans can inspect the exact command surface without repeatedly calling `--help` or rereading the Python source:

- Human-readable reference: `references/cli-reference.md`
- Machine-readable spec: `references/cli-reference.json`

To regenerate both files after changing `scripts/asana_api.py`:

```bash
python3 scripts/generate_cli_docs.py
```

## Updating

The skill auto-updates in the background. To force an update manually, tell your AI:

> Update the Asana skill to the latest version

Or run directly:

```bash
python3 ~/Code/asana-ai-skill/scripts/update_skill.py --force
```

## Requirements

- macOS or Linux (Windows WSL works too)
- Python 3.9+ (pre-installed on most Macs)
- A personal Asana access token (created in Step 1 above)
- Codex, Claude Code, or another agent that supports local skills

No `pip install` step is required — the skill uses only Python's standard library.

---

<details>
<summary><strong>Manual setup (for developers or if you prefer doing it yourself)</strong></summary>

### Option A: Clone and bootstrap

```bash
git clone https://github.com/elibosley/asana-ai-skill.git ~/Code/asana-ai-skill
python3 ~/Code/asana-ai-skill/scripts/bootstrap_skill.py --agent both
```

The bootstrap script will prompt you for your Asana token if one is not already saved.

### Option B: Download ZIP and bootstrap

1. Click the green **Code** button at the top of this page, then **Download ZIP**.
2. Unzip the download.
3. Move the unzipped folder to `~/Code/asana-ai-skill` (rename it if the folder is called `asana-codex-skill-main` or similar).
4. Open Terminal and run:

```bash
python3 ~/Code/asana-ai-skill/scripts/bootstrap_skill.py --agent both
```

### Saving the token manually

If the bootstrap script does not prompt you, save the token yourself:

```bash
mkdir -p ~/.agent-skills/asana
nano ~/.agent-skills/asana/asana_pat
```

Paste your token, then press **Ctrl+X**, then **Y**, then **Enter** to save.

### Single-agent install

- Codex only: `python3 ~/Code/asana-ai-skill/scripts/bootstrap_skill.py --agent codex`
- Claude Code only: `python3 ~/Code/asana-ai-skill/scripts/bootstrap_skill.py --agent claude`

### Verify

```bash
python3 ~/Code/asana-ai-skill/scripts/asana_api.py whoami
```

</details>

<details>
<summary><strong>Maintainer and release workflow</strong></summary>

### Repo structure

- `SKILL.md` plus `agents/openai.yaml` — the skill definitions
- `entrypoints/` — companion workflow skills like `asana-daily-briefing` and `asana-inbox-cleanup`
- `scripts/asana_api.py` — API client (standard library only)
- `scripts/generate_cli_docs.py` — emits parser-derived CLI docs and JSON spec
- `scripts/bootstrap_skill.py` — first-time setup
- `scripts/install_skill.py` — local install or update
- `scripts/update_skill.py` — self-updating installs
- `references/cli-reference.md` — exact CLI reference for humans
- `references/cli-reference.json` — exact CLI spec for agents and sync tests
- `asana-context.example.json` — workspace and team defaults template

### Versioning

This skill uses `MAJOR.MINOR.PATCH.MICRO` versioning in the `VERSION` file with user-facing notes in `CHANGELOG.md`.

```bash
cat VERSION
python3 scripts/check_release.py
python3 scripts/bump_version.py --part auto --title "Short release title"
```

### Release checklist

1. Run `python3 scripts/bump_version.py --part auto --title "Short release title"`.
2. Replace the scaffold text in `CHANGELOG.md` with a real user-facing summary.
3. Run `python3 scripts/check_release.py`.
4. Commit and push only after the release check passes.

The release check fails when skill changes lack `VERSION` and `CHANGELOG.md` updates, when the top changelog entry does not match `VERSION`, or when the changelog still contains scaffold placeholder text.

### Auto-update internals

The self-updater (`scripts/update_skill.py`) supports:

- **Git-backed install**: fast-forwards with `git pull --ff-only`
- **Copy install**: bootstraps a managed clone under `~/.agent-skills/sources/asana-ai-skill`, then switches to a tracked checkout

The skill calls the updater in best-effort mode during normal use with an interval gate to avoid excessive network calls.

### Secret handling

- Shared local state: `~/.agent-skills/asana/`
- Legacy fallback: `~/.codex/skills-data/asana/`
- `.secrets/` and `asana-context.json` are gitignored

### Write output

Write commands return a direct `review_url` in their JSON output so agents can link users to the changed Asana object. Story/comment writes also return `target_review_url` for the parent task.

### Claude Code skill path

Claude Code personal skills live in `~/.claude/skills/<skill-name>/SKILL.md`. The installer places the skill at `~/.claude/skills/asana` when `--agent claude` or `--agent both` is used.

</details>
