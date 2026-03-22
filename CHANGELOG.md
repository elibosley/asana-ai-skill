# Changelog

## [0.1.0.1] - 2026-03-22 — Repo Rename Cleanup

### Changed

- **The skill now points at the renamed GitHub repo everywhere it matters.** Fresh installs and managed clones now prefer `unraid/asana-ai-skill`, setup docs use the new repo name and example checkout path, and bootstrap refresh messaging uses the actual local repo path instead of a stale hard-coded one.

## [0.1.0.0] - 2026-03-22 — Versioned Skill Baseline

### Added

- **Versioned releases for the Asana skill.** The repo now tracks a four-part internal version in `VERSION`, keeps user-facing release notes in `CHANGELOG.md`, and teaches the updater to report version-aware changes instead of only raw git commits.
- **Direct story lookup.** You can now inspect a story or comment by gid with `python3 scripts/asana_api.py story <story_gid>` and get both the story permalink and the parent task link back in one call.
- **Review links in write responses.** Task writes and story/comment writes now return `review_url`, plus `target_review_url` when Asana includes the parent task permalink.

### Changed

- **Assigned-task pulls carry more workflow context.** `project-assigned-tasks` can include section order, task position, recent comments, and attachments so pull lists can be triaged without extra stitching.
- **Auto-update output is version-aware.** When the skill updates, the updater now compares `VERSION` values and can print a concise "what's new" summary from the changelog.

### Fixed

- **AI-authored rich-text comments render with clearer line breaks.** Inline disclaimer-heavy HTML blobs are normalized into a list-based structure before they are posted to Asana, which makes the final comment much more readable.
