# Changelog

## [4.0.2.0] - 2026-04-07 — Move AI disclosure to message footnotes

### Changed

- **AI-authored Asana comments now render their disclosure as a footer instead of a leading banner.** The helper now places the `AI MESSAGE DISCLAIMER` at the bottom of normalized rich-text messages so the actual status, action, and review content appears first in the comment body.
- **Legacy AI-authored message formats now normalize into the new footer layout.** Older single-list, inline-blob, and header-first rich-text payloads are rewritten into the same canonical footer-disclaimer shape so comment updates do not keep resurfacing the disclosure at the top.
- **Regression coverage now locks the new disclosure placement in place.** The rich-text normalization tests now assert both the footer rewrite path and the already-footer-preserving path so future formatting changes do not silently revert the disclosure position.

## [4.0.1.0] - 2026-03-31 — Add parser-derived CLI reference

### Changed

- **The skill now ships a parser-derived CLI reference for exact command discovery.** `references/cli-reference.md` gives agents and humans a compact, committed view of the `asana_api.py` command surface, and `references/cli-reference.json` provides the same data in a machine-readable format for low-context command lookup.
- **CLI reference files are now generated instead of hand-maintained.** `scripts/generate_cli_docs.py` walks the `argparse` tree directly, extracts shared flags and per-command options, and regenerates both reference files from the live parser so command docs stay aligned with the code.
- **Release validation now catches stale CLI docs before a skill update ships.** `scripts/check_release.py` now runs the CLI generator in `--check` mode, and the new regression test locks the committed reference files to the current parser so command mismatches such as unsupported guessed flags are caught locally.

## [4.0.0.0] - 2026-03-31 — Add My Tasks sorter tag normalization

### Changed

- **My Tasks sorter tags now have a dedicated normalization command.** `set-task-sorting-tag` keeps exactly one personal sorter tag such as `Quick Win`, `Delegate`, `Close Out`, `Deep Work`, `Waiting`, or `Needs Clarity` on a task while preserving every unrelated project tag.
- **Task tag writes now resolve human tag names instead of forcing raw gids.** `add-task-tag` and `remove-task-tag` can now take an exact tag name directly, and the helper refreshes workspace tags when the cache is stale so agents can work from the labels users actually say out loud.
- **My Tasks task reads now expose existing tags to the AI layer.** Task bundle and My Tasks review fetches now include tag metadata so a tag-based triage pass can leave correct sorter tags alone instead of blindly reapplying them.
- **Transient DNS failures no longer abort an Asana run immediately.** The API helper now retries bounded name-resolution and timeout failures before surfacing a network error, which makes long read/write passes more resilient when connectivity is briefly unstable.
- **The skill docs now explicitly distinguish tag-based sorting from custom-field sorting.** The base skill instructions, README, recipes, and agent metadata now tell the AI to use native task tags for one-of-many My Tasks sorter labels unless the workspace truly uses a custom field.

## [3.0.0.0] - 2026-03-31 — AI-authored briefings and workflow entrypoints

### Changed

- **Daily briefing markdown is now authored by the AI instead of a Python renderer.** The `daily-briefing` workflow still uses a structured reviewable plan, but the final user-facing output now comes from the plan's `final_markdown` field so the morning briefing can include real links, action framing, and richer semantic detail instead of a fixed Python template.
- **The daily briefing contract is now explicitly AI-gated end to end.** The helper validates the reviewed plan JSON and passes the AI-authored markdown through directly, while the automation docs and regression tests now require `final_markdown` rather than relying on Python-owned prose generation.
- **The installer now ships dedicated workflow entrypoints alongside the base `asana` skill.** Installs now include companion skills such as `asana-daily-briefing`, `asana-inbox-cleanup`, `asana-close-out-sections`, `asana-project-working-set`, `asana-weekly-manager-summary`, and `asana-friday-follow-up-summary` so agents can jump directly into the higher-level workflow specs without rediscovering them from the base skill prompt.
- **Workflow entrypoint installs are now validated and documented.** The install path now fails fast if a companion skill source is missing, the README now advertises the new `/asana-*` entrypoints, and new installer tests cover copy-mode companion skill installs so the workflow surface stays shippable in both install modes.

## [2.0.0.0] - 2026-03-31 — Batch lookup support for read commands

### Changed

- **Lookup-style read commands now support one-or-many gids in a single invocation.** Commands such as `task`, `story`, `project`, `section`, `task-bundle`, `task-status`, `task-stories`, `task-comments`, `task-projects`, `task-tags`, `project-custom-fields`, and `task-custom-fields` now accept multiple gids directly instead of forcing one subprocess per lookup.
- **Bulk lookups now use Asana batch requests under the hood.** The helper chunks request sets to the API batch limit, reuses shared workflow metadata for multi-task status lookups, and avoids redundant project-section fetches when several tasks belong to the same board.
- **The lookup response shape is now consistent for single and multi-item reads.** These commands now return a wrapper with `command`, `count`, and `items`, where each item records the `requested_gid`, the API `status_code`, and the command-specific `result`.
- **The daily briefing and inbox cleanup workflows are now fully AI-gated and backed by dedicated long-form automation specs.** The helper emits plan scaffolds, the docs now separate short recipes from execution-ready automation references, and the supporting tests cover the new planning and manager-comment behavior.

## [1.1.0.0] - 2026-03-30 — Expand automation documentation

### Changed

- **Automation guidance is now organized around short recipes plus full long-form specs.** `references/recipes.md` now stays concise, while `references/automations/` holds the complete source-of-truth docs for reusable automation workflows.
- **The skill now documents multiple reusable workflow patterns in a standardized format.** The docs cover a manager-facing weekly employee summary workflow, a recurring Friday follow-up summary for tasks where the user is involved but not the owner, a full daily briefing command-center workflow, an inbox-cleanup PM workflow, a close-out-sections cleanup workflow, and a project-assigned working-set triage workflow.
- **The new automation specs are execution-oriented.** They include placeholders, output contracts, scheduling guidance, deterministic classification rules, constrained LLM fallback rules, validation checklists, and the Asana helper commands each workflow is expected to use.
- **The documentation examples were generalized.** The final examples use reusable placeholders and generic identifiers while preserving the actual automation structure and execution guidance.
- **Rich-text mention handling is now explicitly documented.** The docs call out that the wrapper supports `html_text` comments but not a dedicated mention flag, and they explain when to fall back to the raw stories endpoint for mentions.

## [1.0.1.1] - 2026-03-26 — Personal Repo Source Of Truth

### Changed

- **Install and update guidance now consistently points at the personal GitHub repo.** README setup prompts and manual clone instructions now reference `elibosley/asana-ai-skill`, and the self-updater now seeds managed clones from that same personal repo so future refreshes follow the documented source of truth.

## [1.0.1.0] - 2026-03-25 — Rewrite README for non-technical users

### Changed

- **README rewritten around a non-technical setup flow.** The AI-assisted "paste this block" setup is now Step 2 instead of buried below the manual instructions. Token creation has explicit click-by-click steps. A new "Try It Out" section shows example prompts immediately after install so users know what to do next. Manual setup, maintainer workflows, and release tooling moved into collapsible sections at the bottom. Based on user testing with a first-time non-technical installer.

## [1.0.0.0] - 2026-03-25 — Workflow advisor and rule triggers

### Changed

- **Board view now supports workflow context analysis.** `board <project_gid> --context` enriches the standard board output with per-section task counts, custom field coverage stats, due date coverage, assignee distribution, and staleness buckets (7/14/30+ days) so the AI layer can detect bottlenecks and recommend Asana rules.
- **Existing Asana rules can now be triggered programmatically.** `trigger-rule <trigger_identifier> --task <task_gid>` fires rules configured with "Incoming web request" triggers, with optional `--action-data key=value` pairs for dynamic variables.
- **New workflow patterns reference guides AI-driven rule recommendations.** `references/workflow-patterns.md` documents common bottleneck patterns (section pile-ups, stale tasks, missing fields) with specific Asana rule templates and step-by-step UI creation instructions.

## [0.4.0.0] - 2026-03-24 — Daily briefing mode

### Changed

- **My Tasks now has a dedicated daily briefing command for morning planning.** `python3 scripts/asana_api.py daily-briefing` builds a read-only command center over open My Tasks, and `--markdown` renders it as a link-rich briefing with buckets like `Execute Now`, `Release / Ship Watch`, `Needs Verification`, `Needs Follow-Up`, and `Background / Not Today`.
- **Done-like project columns no longer masquerade as fresh execution work in the morning plan.** When a task has code or PR context but its project state already says things like `Test`, `Staging`, `QA`, or `Production`, the briefing now keeps it in ship-watch or verification buckets instead of telling the agent to start implementing again.
- **The skill now advertises and documents the morning command center workflow directly.** Discovery hints, maintainer instructions, cookbook recipes, and the OpenAI metadata now all steer agents toward `daily-briefing` for a full morning overview and reserve `inbox-cleanup` for the more active personal PM triage flow.

## [0.3.0.0] - 2026-03-23 — Semantic Release Bump Guidance

### Changed

- **The release helper now recommends semantic version bumps from the current diff instead of defaulting everything to micro.** `scripts/bump_version.py` supports `--part auto`, classifies the current repo changes into `major`, `minor`, `patch`, or `micro` from the changed files and public CLI surface, and reports the reasoning so maintainers can keep release bumps aligned with what actually changed.
- **Version bumps now always end with commit-and-push guidance.** After writing `VERSION` and scaffolding `CHANGELOG.md`, the helper now prints explicit next steps for running the release check, committing the release, and pushing the branch, and the maintainer docs plus release-check failure guidance now steer agents toward that full workflow.

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

- **The skill now points at the renamed GitHub repo everywhere it matters.** Fresh installs and managed clones now prefer `elibosley/asana-ai-skill`, setup docs use the new repo name and example checkout path, and bootstrap refresh messaging uses the actual local repo path instead of a stale hard-coded one.

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
