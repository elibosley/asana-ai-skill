# Changelog

## [0.1.0.5] - 2026-03-22 — Release Guard For Skill Updates

### Changed

- **Maintainers now get a hard release gate before pushing skill changes.** The skill instructions explicitly require a versioned release workflow, and the new `python3 scripts/check_release.py` command fails when a skill diff is missing `VERSION` plus `CHANGELOG.md`, when the top changelog entry does not match `VERSION`, or when the scaffold placeholder text has not been replaced with a real release note.

## [0.1.0.4] - 2026-03-22 — Active My Tasks Inbox Cleanup

### Changed

- **My Tasks cleanup is now an active AI triage flow instead of a simple sorter.** The skill can size up a user's My Tasks queue on first run, advertise the right next steps, sort tasks into review sections, re-analyze comments and linked PRs, infer work type plus `active_ai_action` recommendations, and keep manager-style comments off shared tasks unless a task is clearly private.

## [0.1.0.3] - 2026-03-22 — Compact AI Rich Text Markup

### Fixed

- **AI-authored list sections no longer carry indentation whitespace that can show up as empty bullets in Asana.** The formatter now compacts already-structured disclaimer markup before posting, so `What changed` and `Verification` lists are stored without newline-only list artifacts.

## [0.1.0.2] - 2026-03-22 — AI Comment Formatting Cleanup

### Fixed

- **AI-authored Asana updates no longer collapse into one giant bullet list.** The rich-text normalizer now rewrites the older single-list disclaimer format into mixed block/list sections, preserves already-structured comments, and the recommended templates now use blockquote-style narrative lines with lists only where bullets are actually warranted.

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
