#!/usr/bin/env python3
"""
Fail if a shipped skill change is missing VERSION/CHANGELOG updates.

This is intentionally lightweight so agents can run it before commit/push.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
VERSION_FILE = REPO_ROOT / "VERSION"
CHANGELOG_FILE = REPO_ROOT / "CHANGELOG.md"
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)$")
CHANGELOG_HEADER_RE = re.compile(r"^## \[([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\] - ")
CHANGELOG_PLACEHOLDER = "Describe the user-visible change here."
RELEASE_FILES = {"VERSION", "CHANGELOG.md"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check that skill changes include a version bump and changelog entry")
    parser.add_argument("--base", default="origin/main", help="Git base ref to compare against; defaults to origin/main")
    parser.add_argument("--head", default="HEAD", help="Git head ref to compare; defaults to HEAD")
    return parser.parse_args()


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def resolve_diff_range(base: str, head: str) -> tuple[str | None, str]:
    try:
        run_git("rev-parse", "--verify", base)
        return base, head
    except RuntimeError:
        try:
            fallback = run_git("rev-parse", "--verify", "HEAD~1")
            return fallback, head
        except RuntimeError:
            return None, head


def changed_files(base: str | None, head: str) -> list[str]:
    if base:
        output = run_git("diff", "--name-only", f"{base}...{head}")
    else:
        output = run_git("diff-tree", "--no-commit-id", "--name-only", "-r", head)
    return [line.strip() for line in output.splitlines() if line.strip()]


def working_tree_files() -> list[str]:
    unstaged = run_git("diff", "--name-only")
    staged = run_git("diff", "--cached", "--name-only")
    combined = {line.strip() for line in (unstaged.splitlines() + staged.splitlines()) if line.strip()}
    return sorted(combined)


def read_version() -> str:
    value = VERSION_FILE.read_text().strip()
    if not VERSION_RE.fullmatch(value):
        raise SystemExit(f"Invalid VERSION value: {value!r}")
    return value


def read_top_changelog_block() -> tuple[str | None, str]:
    content = CHANGELOG_FILE.read_text()
    lines = content.splitlines()
    start_index = None
    top_version = None
    for index, line in enumerate(lines):
        match = CHANGELOG_HEADER_RE.match(line)
        if match:
            start_index = index
            top_version = match.group(1)
            break
    if start_index is None:
        return None, ""

    block_lines: list[str] = []
    for line in lines[start_index:]:
        if block_lines and line.startswith("## "):
            break
        block_lines.append(line)
    return top_version, "\n".join(block_lines)


def fail(message: str) -> None:
    raise SystemExit(
        f"{message}\n\n"
        "Fix:\n"
        '  python3 scripts/bump_version.py --part auto --title "Short release title"\n'
        "  edit CHANGELOG.md to replace the scaffold text with a real user-facing summary\n"
        "  python3 scripts/check_release.py\n"
        '  git commit -m "chore(asana): release vX.Y.Z.W"\n'
        "  git push origin <branch>\n"
    )


def main() -> None:
    args = parse_args()
    base, head = resolve_diff_range(args.base, args.head)
    files = sorted(set(changed_files(base, head)) | set(working_tree_files()))

    if not files:
        print("release-check: no changed files")
        return

    changed = set(files)
    non_release_files = sorted(path for path in changed if path not in RELEASE_FILES)

    if non_release_files and not RELEASE_FILES.issubset(changed):
        fail(
            "release-check: skill changes detected without both VERSION and CHANGELOG.md in the diff.\n"
            f"Changed files: {', '.join(files)}"
        )

    version = read_version()
    top_version, top_block = read_top_changelog_block()

    if top_version != version:
        fail(
            "release-check: top CHANGELOG entry does not match VERSION.\n"
            f"VERSION={version}, CHANGELOG top={top_version or 'missing'}"
        )

    if CHANGELOG_PLACEHOLDER in top_block:
        fail("release-check: top CHANGELOG entry still contains the scaffold placeholder text.")

    print(
        "release-check: ok\n"
        f"base={base or 'single-commit'} head={head}\n"
        f"version={version}\n"
        f"changed_files={len(files)}"
    )


if __name__ == "__main__":
    main()
