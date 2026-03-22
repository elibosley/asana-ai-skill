# Asana Codex Skill

Portable Asana skill for Codex-style agents. The repo contains the skill itself, a local installer, and setup instructions that keep tokens out of git.

## What is included

- `SKILL.md` plus `agents/openai.yaml`
- `scripts/asana_api.py` with only Python standard-library dependencies
- `scripts/install_skill.py` for local install or update
- `scripts/update_skill.py` for self-updating installs
- `asana-context.example.json` for workspace and team defaults

## Requirements

- Python `3.10+`
- A personal Asana access token
- Codex or another agent environment that supports local skills

No `pip install` step is required.

## Best install path for maintainers

Clone this repo into `~/Code/asana-codex-skill`, then run:

```bash
python3 scripts/install_skill.py --mode symlink --replace
```

That makes `~/.codex/skills/asana` point at this repo, so a later `git pull` updates the live skill.

## Auto-update

The skill now ships with a self-updater:

```bash
python3 scripts/update_skill.py --force
```

It supports two cases:

- Symlink or git-backed install: fast-forwards the local checkout with `git pull --ff-only`
- Copy install: bootstraps a managed clone under `~/.codex/skill-sources/asana-codex-skill`, then switches `~/.codex/skills/asana` to that tracked checkout

The skill can also call the updater in best-effort mode during normal use, with a built-in interval gate so it does not hit the network every single invocation.

## AI-friendly install prompt

Paste this into your AI tool instead of asking people to run raw setup commands:

```text
Install the `asana` skill from the GitHub repo `Unraid/asana-codex-skill`, then set it up locally for me.

Requirements:
- Install it into `~/.codex/skills/asana`
- Prefer a symlink install if the repo is already cloned locally; otherwise install from GitHub
- Confirm `python3` is available and do not add any pip dependencies unless they are actually needed
- Enable the skill's built-in auto-update path
- Keep secrets out of git
- Configure auth with either `ASANA_ACCESS_TOKEN` or `~/.codex/skills-data/asana/asana_pat`
- If `~/.codex/skills-data/asana/asana-context.json` does not exist, create it from `asana-context.example.json`
- Verify the install by running `python3 scripts/asana_api.py whoami`
- Verify the updater by running `python3 scripts/update_skill.py --force`
- Never print the token in output
```

## Manual setup

1. Put your token in `ASANA_ACCESS_TOKEN`, or create `~/.codex/skills-data/asana/asana_pat`.
2. Copy `asana-context.example.json` to `~/.codex/skills-data/asana/asana-context.json`.
3. Fill in your workspace, team, and optional user defaults.
4. Run `python3 scripts/asana_api.py whoami`.
5. Run `python3 scripts/update_skill.py --force`.

## Updating

- Any install: `python3 scripts/update_skill.py --force`
- Symlink install: `git -C ~/Code/asana-codex-skill pull --ff-only`
- Copy install: the updater will convert it to a managed git-backed install automatically
- GitHub install through AI: ask the AI to reinstall or refresh the skill from the repo

## Secret handling

- Default local state lives in `~/.codex/skills-data/asana/`
- `.secrets/` is still gitignored for backward compatibility
- `asana-context.json` in the repo is gitignored for backward compatibility
- The repo ships only `asana-context.example.json`
