# Changelog

## [0.2.0.0] - 2026-03-23 — Personal PM Inbox Triage

### Changed

- **`inbox-cleanup` is now positioned as a personal PM workflow for My Tasks, not just a sorter.** The helper and skill docs now frame it around classifying what each task really is, proposing next actions and TODOs, surfacing what AI can execute now, and only posting manager-style comments when the task looks truly private to the assignee.
- **Stale personal sections can now be retired with a dedicated close-out command.** The new `close-out-sections` workflow previews exact source sections, can move all/completed/incomplete tasks into a destination section, and deletes the original section only after it is confirmed empty, including clearer handling for non-removable My Tasks sections like `Recently assigned`.
- **The skill is easier to install on older local runtimes.** Bootstrap and install now support Python 3.9+, and the updater avoids newer `datetime` APIs so managed refresh flows still work on older supported interpreters.

## [0.1.0.10] - 2026-03-23 — Lower Python Version Floor

### Changed

- **The skill now supports Python 3.9+ instead of effectively requiring newer runtimes.** The bootstrap and install scripts now accept Python 3.9+, the README matches that lower floor, and the updater uses `timezone.utc` instead of the newer `datetime.UTC` constant so refresh workflows still run on older supported interpreters.

## [0.1.0.9] - 2026-03-22 — Stricter Private PM Comment Guardrail

### Fixed

- **Personal PM comments now require a truly private task context.** The inbox cleanup helper will no longer post manager-plan comments just because a task lacks project membership; it now blocks those comments when the task has shared project context, a parent task, non-assignee followers/collaborators, or comment history from anyone other than the assignee.

## [0.1.0.8] - 2026-03-22 — Document Non-Removable Recently Assigned

### Changed

- **The skill now documents that My Tasks `Recently assigned` may be emptyable but still non-removable.** The core skill instructions, cookbook, and README now tell agents to treat that column as a special case: drain it to zero tasks when asked, but if Asana refuses deletion afterward, report it as emptied rather than retrying forever.

## [0.1.0.7] - 2026-03-22 — Inbox Cleanup As Personal PM

### Changed

- **Inbox cleanup is now documented as the preferred personal PM workflow for My Tasks.** The skill instructions, cookbook, UI metadata, and helper descriptions now steer agents to use `inbox-cleanup` not just for filing tasks into sections, but for classifying what each task is, proposing next actions and TODOs, and identifying what the AI can help execute immediately.

## [0.1.0.6] - 2026-03-22 — Section Close-Out Workflow

### Changed

- **The skill can now retire stale Asana sections in one guided step.** The new `close-out-sections` command previews exact source sections, can relocate all tasks or only completed/incomplete tasks into another section, and deletes the original section only after it passes a final empty check. The helper docs and examples now also call out this workflow for My Tasks cleanup and personal category cleanup.

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
