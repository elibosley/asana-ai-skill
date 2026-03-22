#!/usr/bin/env python3
"""
Bump the Asana skill version and optionally prepend a changelog scaffold.

Follows gstack's 4-part version format: MAJOR.MINOR.PATCH.MICRO
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
VERSION_FILE = REPO_ROOT / "VERSION"
CHANGELOG_FILE = REPO_ROOT / "CHANGELOG.md"
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bump the Asana skill VERSION and scaffold CHANGELOG")
    parser.add_argument(
        "--part",
        choices=("major", "minor", "patch", "micro"),
        default="micro",
        help="Version part to bump; defaults to micro",
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


def main() -> None:
    args = parse_args()
    current = read_version()
    new_version = validate_version(args.set_version) if args.set_version else bump_version(current, args.part)
    VERSION_FILE.write_text(f"{new_version}\n")

    if not args.skip_changelog and args.title:
        prepend_changelog_entry(new_version, args.date, args.title)

    print(f"{current} -> {new_version}")
    if not args.skip_changelog:
        if args.title:
            print(f"Prepended CHANGELOG scaffold for v{new_version}: {args.title}")
        else:
            print("VERSION updated. No CHANGELOG entry added because --title was not provided.")


if __name__ == "__main__":
    main()
