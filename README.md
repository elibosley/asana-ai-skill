# Asana Agent Skill

Portable Asana skill for Codex, Claude Code, and similar local coding agents. The repo contains the skill itself, a local installer, and setup instructions that keep tokens out of git.

## Start Here

If you are a non-technical Asana admin, start here.

1. Sign in to [Asana](https://app.asana.com/).
2. Create a personal access token from profile photo -> `Settings` -> `Apps` -> `View developer console` -> `Personal access tokens` -> `Create new token`.
3. Save that token to `~/.agent-skills/asana/asana_pat`.
4. Run:

```bash
python3 ~/Code/asana-codex-skill/scripts/bootstrap_skill.py --agent both
```

That bootstrap step installs the skill for both Codex and Claude Code, creates shared local storage, builds your Asana context automatically, and verifies access.

If you want your AI tool to do almost all of this for you, paste this:

```text
Set up the private `asana` skill for me from `Unraid/asana-codex-skill` with as little manual work as possible.

Requirements:
- Ask me first which agent I want this installed for: `Codex`, `Claude Code`, or `both`
- If `~/Code/asana-codex-skill` does not exist, clone the repo there. If it does exist, update it safely.
- Confirm `python3` is available and do not add any pip dependencies unless they are actually needed
- After I answer, run the matching bootstrap command:
  - Codex: `python3 ~/Code/asana-codex-skill/scripts/bootstrap_skill.py --agent codex`
  - Claude Code: `python3 ~/Code/asana-codex-skill/scripts/bootstrap_skill.py --agent claude`
  - Both: `python3 ~/Code/asana-codex-skill/scripts/bootstrap_skill.py --agent both`
- Keep secrets out of git
- Install only the agent target I chose
- Enable the built-in auto-update path
- Use `~/.agent-skills/asana/` for token and context storage
- If `~/.agent-skills/asana/asana_pat` is missing, walk me through signing into Asana and creating one:
  sign in to `https://app.asana.com/`, then go to profile photo -> `Settings` -> `Apps` -> `View developer console` -> `Personal access tokens` -> `Create new token`
- Explain that the token is shown once and should be saved immediately
- Save the token to `~/.agent-skills/asana/asana_pat` with safe file permissions
- After the token is in place, rerun the bootstrap script so it can auto-build `asana-context.json`
- Verify the install by running `python3 ~/Code/asana-codex-skill/scripts/asana_api.py whoami`
- Verify the updater by running `python3 ~/Code/asana-codex-skill/scripts/update_skill.py --force`
- Never print the token in output
```

If you only want one agent:

- Codex only: `python3 ~/Code/asana-codex-skill/scripts/bootstrap_skill.py --agent codex`
- Claude Code only: `python3 ~/Code/asana-codex-skill/scripts/bootstrap_skill.py --agent claude`

## What Is Included

- `SKILL.md` plus `agents/openai.yaml`
- `scripts/asana_api.py` with only Python standard-library dependencies
- `scripts/bootstrap_skill.py` for first-time setup
- `scripts/install_skill.py` for local install or update
- `scripts/update_skill.py` for self-updating installs
- `asana-context.example.json` for workspace and team defaults

## Requirements

- Python `3.10+`
- A personal Asana access token
- Codex, Claude Code, or another agent environment that supports local skills

No `pip install` step is required.

## Maintainer Setup

Clone this repo into `~/Code/asana-codex-skill`, then run:

```bash
python3 scripts/bootstrap_skill.py --agent both
```

That installs the skill, creates the shared local state directory, refreshes the repo when safe, and auto-builds `asana-context.json` if a token is already present.

## Admin Setup

For non-technical admins, the bootstrap script is the main entry point:

```bash
python3 ~/Code/asana-codex-skill/scripts/bootstrap_skill.py --agent both
```

It handles almost everything automatically and leaves only the token step if the user has not added one yet.

Claude Code personal skills live in `~/.claude/skills/<skill-name>/SKILL.md`, so this installer places the skill at `~/.claude/skills/asana` when `--agent claude` or `--agent both` is used.

## Getting an Asana token

If the user does not already have a token, they need to sign in to Asana first and create one from the developer console:

1. Sign in to [Asana](https://app.asana.com/).
2. Click your profile photo.
3. Open `Settings`.
4. Go to the `Apps` tab.
5. Click `View developer console`.
6. In `Personal access tokens`, click `Create new token`.
7. Name the token, accept the API terms, and create it.
8. Copy the token immediately and save it to `~/.agent-skills/asana/asana_pat`.

Important notes:

- The token is shown once, so copy it right away.
- A PAT acts as the signed-in user.
- It can access the Asana workspaces that user is already a member of.

## Auto-update

The skill now ships with a self-updater:

```bash
python3 scripts/update_skill.py --force
```

It supports two cases:

- Symlink or git-backed install: fast-forwards the local checkout with `git pull --ff-only`
- Copy install: bootstraps a managed clone under `~/.agent-skills/sources/asana-codex-skill`, then switches the installed skill directories to that tracked checkout

The skill can also call the updater in best-effort mode during normal use, with a built-in interval gate so it does not hit the network every single invocation.

## Manual setup

1. Clone the repo to `~/Code/asana-codex-skill`.
2. Sign in to Asana and create a PAT from `Settings` -> `Apps` -> `View developer console` -> `Personal access tokens` -> `Create new token`.
3. Save that PAT to `~/.agent-skills/asana/asana_pat`.
4. Run `python3 ~/Code/asana-codex-skill/scripts/bootstrap_skill.py --agent both`.

## Updating

- Any install: `python3 scripts/update_skill.py --force`
- First-time setup or repair: `python3 scripts/bootstrap_skill.py --agent both`
- Symlink install: `git -C ~/Code/asana-codex-skill pull --ff-only`
- Copy install: the updater will convert it to a managed git-backed install automatically
- GitHub install through AI: ask the AI to reinstall or refresh the skill from the repo

## Secret handling

- Default shared local state lives in `~/.agent-skills/asana/`
- The helper still falls back to the legacy `~/.codex/skills-data/asana/` path for backward compatibility
- `.secrets/` is still gitignored for backward compatibility
- `asana-context.json` in the repo is gitignored for backward compatibility
- The repo ships only `asana-context.example.json`
