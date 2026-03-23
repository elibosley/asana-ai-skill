#!/usr/bin/env python3
"""
Bump the Asana skill version and optionally prepend a changelog scaffold.

Follows gstack's 4-part version format: MAJOR.MINOR.PATCH.MICRO
"""

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import date
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
VERSION_FILE = REPO_ROOT / "VERSION"
CHANGELOG_FILE = REPO_ROOT / "CHANGELOG.md"
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)$")
RELEASE_FILES = {"VERSION", "CHANGELOG.md"}
DOCS_ONLY_PREFIXES = ("references/",)
DOCS_ONLY_FILES = {"README.md", "SKILL.md", "agents/openai.yaml"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bump the Asana skill VERSION and scaffold CHANGELOG")
    parser.add_argument(
        "--part",
        choices=("auto", "major", "minor", "patch", "micro"),
        default="auto",
        help="Version part to bump; defaults to auto based on the current diff",
    )
    parser.add_argument(
        "--set-version",
        help="Explicitly set VERSION instead of bumping a part",
    )
    parser.add_argument(
        "--title",
        help="Optional changelog title to prepend for the new version",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Release date for the changelog entry (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--skip-changelog",
        action="store_true",
        help="Update VERSION only",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Git base ref to compare against when --part auto is used; defaults to origin/main",
    )
    parser.add_argument(
        "--head",
        default="HEAD",
        help="Git head ref to compare against when --part auto is used; defaults to HEAD",
    )
    return parser.parse_args()


def read_version() -> str:
    if not VERSION_FILE.exists():
        raise SystemExit(f"Missing VERSION file: {VERSION_FILE}")
    value = VERSION_FILE.read_text().strip()
    if not VERSION_RE.fullmatch(value):
        raise SystemExit(f"Invalid VERSION value: {value!r}")
    return value


def bump_version(value: str, part: str) -> str:
    major, minor, patch, micro = (int(piece) for piece in value.split("."))
    if part == "major":
        major, minor, patch, micro = major + 1, 0, 0, 0
    elif part == "minor":
        major, minor, patch, micro = major, minor + 1, 0, 0
    elif part == "patch":
        major, minor, patch, micro = major, minor, patch + 1, 0
    else:
        major, minor, patch, micro = major, minor, patch, micro + 1
    return f"{major}.{minor}.{patch}.{micro}"


def validate_version(value: str) -> str:
    token = value.strip()
    if not VERSION_RE.fullmatch(token):
        raise SystemExit("Version must use MAJOR.MINOR.PATCH.MICRO format, e.g. 0.1.0.1")
    return token


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


def combined_diff_text(base: str | None, head: str) -> str:
    chunks: list[str] = []
    if base:
        range_diff = run_git("diff", "--unified=0", f"{base}...{head}")
    else:
        range_diff = run_git("diff-tree", "--no-commit-id", "-r", "--patch", "--unified=0", head)
    if range_diff:
        chunks.append(range_diff)

    unstaged = run_git("diff", "--unified=0")
    if unstaged:
        chunks.append(unstaged)

    staged = run_git("diff", "--cached", "--unified=0")
    if staged:
        chunks.append(staged)
    return "\n".join(chunks)


def is_docs_only_file(path: str) -> bool:
    if path in RELEASE_FILES or path in DOCS_ONLY_FILES:
        return True
    return any(path.startswith(prefix) for prefix in DOCS_ONLY_PREFIXES)


def classify_release_part(changed: set[str], diff_text: str) -> tuple[str, list[str]]:
    non_release = {path for path in changed if path not in RELEASE_FILES}
    if not non_release:
        return "micro", ["Only VERSION/CHANGELOG release metadata changed."]

    diff_lines = diff_text.splitlines()
    major_reasons: list[str] = []
    if any(
        re.match(r"^[+-](?![+-]).*\bbreaking change\b", line, flags=re.IGNORECASE)
        or re.match(r"^[+-](?![+-]).*\bbreaking:", line, flags=re.IGNORECASE)
        for line in diff_lines
    ):
        major_reasons.append("Diff includes an explicit breaking-change marker.")
    if any(re.match(r"^-[^-].*subparsers\.add_parser\(", line) for line in diff_lines):
        major_reasons.append("Diff removes public CLI subcommand surface.")
    if any(re.match(r"^-[^-].*add_argument\(", line) for line in diff_lines):
        major_reasons.append("Diff removes public CLI flag or argument surface.")
    if major_reasons:
        return "major", major_reasons

    minor_reasons: list[str] = []
    if any(re.match(r"^\+\+\+ b/scripts/.+\.py$", line) for line in diff_lines):
        pass
    if any(re.match(r"^\+[^+].*subparsers\.add_parser\(", line) for line in diff_lines):
        minor_reasons.append("Diff adds a new public CLI subcommand.")
    if any(re.match(r"^\+[^+].*add_argument\(", line) for line in diff_lines):
        minor_reasons.append("Diff adds new public CLI flags or arguments.")
    if any(path.startswith("scripts/") and path.endswith(".py") for path in non_release) and any(
        path.startswith("tests/") for path in non_release
    ):
        minor_reasons.append("Diff adds shipped maintainer functionality with matching regression coverage.")
    if minor_reasons:
        return "minor", minor_reasons

    if any(path.startswith("scripts/") and path.endswith(".py") for path in non_release):
        return "patch", ["Diff changes shipped script behavior without adding new public CLI surface."]

    if any(path.startswith("tests/") for path in non_release):
        return "patch", ["Diff adds or updates automated test coverage."]

    if all(is_docs_only_file(path) for path in non_release):
        return "micro", ["Diff only changes docs, prompts, or release metadata."]

    return "patch", ["Diff changes shipped skill behavior and is safest to treat as a patch."]


def recommend_release_part(base: str, head: str) -> tuple[str, list[str]]:
    resolved_base, resolved_head = resolve_diff_range(base, head)
    files = sorted(set(changed_files(resolved_base, resolved_head)) | set(working_tree_files()))
    diff_text = combined_diff_text(resolved_base, resolved_head)
    return classify_release_part(set(files), diff_text)


def prepend_changelog_entry(version: str, release_date: str, title: str) -> None:
    if not CHANGELOG_FILE.exists():
        existing = "# Changelog\n"
    else:
        existing = CHANGELOG_FILE.read_text()

    header = "# Changelog"
    body = existing
    if existing.startswith(header):
        body = existing[len(header):].lstrip("\n")

    entry = (
        f"## [{version}] - {release_date} — {title}\n\n"
        "### Changed\n\n"
        "- Describe the user-visible change here.\n\n"
    )
    CHANGELOG_FILE.write_text(f"{header}\n\n{entry}{body.lstrip()}")


def current_branch() -> str:
    try:
        branch = run_git("branch", "--show-current")
    except RuntimeError:
        return "<branch>"
    return branch or "<branch>"


def print_next_steps(new_version: str) -> None:
    branch = current_branch()
    print("Next steps:")
    print("1. Replace the scaffold text in CHANGELOG.md with a real user-facing summary.")
    print("2. Run: python3 scripts/check_release.py")
    print("3. Review the staged/uncommitted changes with: git status")
    print('4. Commit the release, for example: git commit -m "chore(asana): release v%s"' % new_version)
    print(f"5. Push the release branch: git push origin {branch}")


def main() -> None:
    args = parse_args()
    current = read_version()
    recommended_part = None
    recommended_reasons: list[str] = []
    if args.set_version:
        new_version = validate_version(args.set_version)
    else:
        chosen_part = args.part
        if args.part == "auto":
            recommended_part, recommended_reasons = recommend_release_part(args.base, args.head)
            chosen_part = recommended_part
        else:
            recommended_part, recommended_reasons = recommend_release_part(args.base, args.head)
        new_version = bump_version(current, chosen_part)
    VERSION_FILE.write_text(f"{new_version}\n")

    if not args.skip_changelog and args.title:
        prepend_changelog_entry(new_version, args.date, args.title)

    print(f"{current} -> {new_version}")
    if recommended_part:
        print(f"Recommended bump: {recommended_part}")
        for reason in recommended_reasons:
            print(f"- {reason}")
        if args.part != "auto" and args.part != recommended_part:
            print(f"Using requested part override: {args.part}")
    if not args.skip_changelog:
        if args.title:
            print(f"Prepended CHANGELOG scaffold for v{new_version}: {args.title}")
        else:
            print("VERSION updated. No CHANGELOG entry added because --title was not provided.")
    print_next_steps(new_version)


if __name__ == "__main__":
    main()
