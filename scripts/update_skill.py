#!/usr/bin/env python3
"""
Best-effort updater for the Asana skill.

- For git-backed installs, fast-forwards the current checkout.
- For copied installs, bootstraps a managed clone under ~/.agent-skills/sources
  and re-points the selected agent skill directories at that checkout.
- Tracks a last-check timestamp so the skill can safely invoke this on use.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
LOCAL_STATE_DIR = Path.home() / ".agent-skills" / "asana"
LEGACY_LOCAL_STATE_DIR = Path.home() / ".codex" / "skills-data" / "asana"
MANAGED_SOURCE_DIR = Path.home() / ".agent-skills" / "sources" / "asana-ai-skill"
STATE_FILE = LOCAL_STATE_DIR / "auto-update.json"
DEFAULT_BRANCH = "main"
DEFAULT_INTERVAL_MINUTES = 360
VERSION_FILE_NAME = "VERSION"
CHANGELOG_FILE_NAME = "CHANGELOG.md"
REPO_URL_CANDIDATES = [
    "git@github.com:unraid/asana-ai-skill.git",
    "https://github.com/unraid/asana-ai-skill.git",
    "git@github.com:unraid/asana-codex-skill.git",
    "https://github.com/unraid/asana-codex-skill.git",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update the Asana skill in place")
    parser.add_argument("--force", action="store_true", help="Ignore the update interval gate")
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=DEFAULT_INTERVAL_MINUTES,
        help="Minimum time between automatic update checks",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress routine output when there is nothing to do",
    )
    parser.add_argument(
        "--best-effort",
        action="store_true",
        help="Never fail hard; print or suppress the error and exit successfully",
    )
    return parser.parse_args()


def run_git(args: list[str], *, cwd: Path, quiet: bool = False) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    output = completed.stdout.strip()
    if output and not quiet:
        print(output)
    return output


def read_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        return {}


def write_state(state: dict[str, str]) -> None:
    LOCAL_STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
    if LEGACY_LOCAL_STATE_DIR.exists():
        LEGACY_LOCAL_STATE_DIR.mkdir(parents=True, exist_ok=True)


def now_utc() -> datetime:
    return datetime.now(UTC)


def version_file(repo_root: Path) -> Path:
    return repo_root / VERSION_FILE_NAME


def changelog_file(repo_root: Path) -> Path:
    return repo_root / CHANGELOG_FILE_NAME


def read_version(repo_root: Path) -> str | None:
    file_path = version_file(repo_root)
    if not file_path.exists():
        return None
    value = file_path.read_text().strip()
    return value or None


def parse_version(value: str | None) -> tuple[int, ...] | None:
    token = str(value or "").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", token):
        return None
    return tuple(int(part) for part in token.split("."))


def changelog_entries(repo_root: Path) -> list[dict[str, str]]:
    file_path = changelog_file(repo_root)
    if not file_path.exists():
        return []

    text = file_path.read_text()
    header_pattern = re.compile(
        r"^## \[(?P<version>[^\]]+)\] - (?P<date>\d{4}-\d{2}-\d{2})(?: — (?P<title>.+))?$",
        re.MULTILINE,
    )
    matches = list(header_pattern.finditer(text))
    entries: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        entries.append(
            {
                "version": match.group("version").strip(),
                "date": match.group("date").strip(),
                "title": (match.group("title") or "").strip(),
                "body": text[body_start:body_end].strip(),
            }
        )
    return entries


def entries_between_versions(repo_root: Path, old_version: str | None, new_version: str | None) -> list[dict[str, str]]:
    new_tuple = parse_version(new_version)
    if new_tuple is None:
        return []

    old_tuple = parse_version(old_version)
    selected: list[dict[str, str]] = []
    for entry in changelog_entries(repo_root):
        entry_tuple = parse_version(entry.get("version"))
        if entry_tuple is None:
            continue
        if entry_tuple > new_tuple:
            continue
        if old_tuple is not None and entry_tuple <= old_tuple:
            continue
        selected.append(entry)
    return selected


def summarize_changelog_entries(entries: list[dict[str, str]]) -> str:
    if not entries:
        return ""

    lines = ["What's new:"]
    for entry in entries:
        version = entry.get("version", "").strip()
        title = entry.get("title", "").strip()
        headline = f"- v{version}"
        if title:
            headline += f" — {title}"
        lines.append(headline)

        bullets = [
            line.strip()
            for line in entry.get("body", "").splitlines()
            if line.strip().startswith("- ")
        ]
        for bullet in bullets[:3]:
            lines.append(f"  {bullet}")
    return "\n".join(lines)


def should_check(args: argparse.Namespace, state: dict[str, str]) -> bool:
    if args.force:
        return True
    last_checked_at = state.get("last_checked_at")
    if not last_checked_at:
        return True
    try:
        last = datetime.fromisoformat(last_checked_at)
    except ValueError:
        return True
    return now_utc() - last >= timedelta(minutes=args.interval_minutes)


def repo_root_for(path: Path) -> Path | None:
    try:
        root = run_git(["rev-parse", "--show-toplevel"], cwd=path, quiet=True)
    except subprocess.CalledProcessError:
        return None
    return Path(root)


def repo_has_uncommitted_changes(repo_root: Path) -> bool:
    status = run_git(["status", "--porcelain"], cwd=repo_root, quiet=True)
    return bool(status.strip())


def repo_remote_url(repo_root: Path) -> str | None:
    try:
        return run_git(["remote", "get-url", "origin"], cwd=repo_root, quiet=True)
    except subprocess.CalledProcessError:
        return None


def ensure_origin(repo_root: Path) -> None:
    remote = repo_remote_url(repo_root)
    if remote:
        return
    for candidate in REPO_URL_CANDIDATES:
        try:
            run_git(["remote", "add", "origin", candidate], cwd=repo_root, quiet=True)
            return
        except subprocess.CalledProcessError:
            continue
    raise RuntimeError("Unable to configure a git origin for the Asana skill repo.")


def clone_managed_source() -> Path:
    MANAGED_SOURCE_DIR.parent.mkdir(parents=True, exist_ok=True)
    if MANAGED_SOURCE_DIR.exists():
        return MANAGED_SOURCE_DIR

    for candidate in REPO_URL_CANDIDATES:
        completed = subprocess.run(
            ["git", "clone", candidate, str(MANAGED_SOURCE_DIR)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            return MANAGED_SOURCE_DIR
    raise RuntimeError(
        "Unable to clone the private Asana skill repo. Confirm git access to Unraid/asana-ai-skill."
    )


def install_from_repo(repo_root: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "install_skill.py"),
            "--agent",
            "both",
            "--mode",
            "symlink",
            "--replace",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def fast_forward_repo(repo_root: Path, *, quiet: bool) -> tuple[bool, str, str | None, str | None, str]:
    ensure_origin(repo_root)
    if repo_has_uncommitted_changes(repo_root):
        current_version = read_version(repo_root)
        return False, f"Skipped auto-update because {repo_root} has local changes.", current_version, current_version, ""

    before_version = read_version(repo_root)
    before = run_git(["rev-parse", "HEAD"], cwd=repo_root, quiet=True)
    run_git(["fetch", "--prune", "origin"], cwd=repo_root, quiet=True)
    remote_ref = f"origin/{DEFAULT_BRANCH}"
    try:
        after_remote = run_git(["rev-parse", remote_ref], cwd=repo_root, quiet=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Remote branch {remote_ref} was not found.") from exc

    if before == after_remote:
        current_version = read_version(repo_root)
        message = f"Already up to date at v{current_version}." if current_version else "Already up to date."
        return False, message, current_version, current_version, ""

    run_git(["pull", "--ff-only", "origin", DEFAULT_BRANCH], cwd=repo_root, quiet=True)
    after = run_git(["rev-parse", "--short", "HEAD"], cwd=repo_root, quiet=True)
    after_version = read_version(repo_root)
    changelog_summary = summarize_changelog_entries(
        entries_between_versions(repo_root, before_version, after_version)
    )

    if before_version and after_version and before_version != after_version:
        message = f"Updated Asana skill from v{before_version} to v{after_version} ({after})."
    elif after_version:
        message = f"Updated Asana skill to v{after_version} ({after})."
    else:
        message = f"Updated Asana skill to commit {after}."

    return True, message, before_version, after_version, changelog_summary


def record_check(
    state: dict[str, str],
    *,
    updated: bool,
    message: str,
    version: str | None = None,
    changelog_summary: str = "",
) -> None:
    state["last_checked_at"] = now_utc().isoformat()
    state["last_message"] = message
    if version:
        state["last_version"] = version
    if changelog_summary:
        state["last_changelog_summary"] = changelog_summary
    if updated:
        state["last_updated_at"] = state["last_checked_at"]
    write_state(state)


def update_current_install(args: argparse.Namespace) -> int:
    state = read_state()
    if not should_check(args, state):
        return 0

    repo_root = repo_root_for(SKILL_DIR)
    message = f"Already up to date at v{read_version(SKILL_DIR) or 'unknown'}."
    updated = False
    current_version = read_version(SKILL_DIR)
    changelog_summary = ""

    if repo_root is None:
        repo_root = clone_managed_source()
        updated, message, _before_version, current_version, changelog_summary = fast_forward_repo(
            repo_root,
            quiet=args.quiet,
        )
        install_from_repo(repo_root)
        if not updated:
            current_version = read_version(repo_root)
            message = (
                f"Switched copied install to managed git-backed install at v{current_version}."
                if current_version
                else "Switched copied install to managed git-backed install."
            )
            updated = True
    else:
        updated, message, _before_version, current_version, changelog_summary = fast_forward_repo(
            repo_root,
            quiet=args.quiet,
        )

    record_check(
        state,
        updated=updated,
        message=message,
        version=current_version,
        changelog_summary=changelog_summary,
    )
    if not args.quiet or updated:
        print(message)
        if changelog_summary:
            print()
            print(changelog_summary)
    return 0


def main() -> int:
    args = parse_args()
    try:
        return update_current_install(args)
    except Exception as exc:  # noqa: BLE001
        if args.best_effort:
            if not args.quiet:
                print(f"Auto-update skipped: {exc}")
            return 0
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
