#!/usr/bin/env python3
"""
Install or update the Asana skill into ~/.codex/skills/asana.

Defaults to a symlink install so pulling the repo updates the active skill.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEST = Path.home() / ".codex" / "skills" / "asana"
LOCAL_STATE_DIR = Path.home() / ".codex" / "skills-data" / "asana"
PRESERVED_FILES = [
    (".secrets/asana_pat", False),
    ("asana-context.json", True),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the Asana Codex skill locally")
    parser.add_argument(
        "--mode",
        choices=("symlink", "copy"),
        default="symlink",
        help="Install as a symlink for easy updates, or copy files into place",
    )
    parser.add_argument(
        "--dest",
        default=str(DEFAULT_DEST),
        help="Destination skill directory",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing install and preserve local token/context files when possible",
    )
    return parser.parse_args()


def ensure_python() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10+ is required.")


def preserve_local_files(dest: Path, stash_dir: Path) -> None:
    for relative_path, optional in PRESERVED_FILES:
        source = dest / relative_path
        if not source.exists():
            if optional:
                continue
            continue
        target = stash_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def restore_local_files(stash_dir: Path) -> None:
    LOCAL_STATE_DIR.mkdir(parents=True, exist_ok=True)
    mapping = {
        ".secrets/asana_pat": LOCAL_STATE_DIR / "asana_pat",
        "asana-context.json": LOCAL_STATE_DIR / "asana-context.json",
    }
    for relative_path, target in mapping.items():
        source = stash_dir / relative_path
        if not source.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def remove_existing(dest: Path) -> None:
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
        return
    shutil.rmtree(dest)


def install_symlink(dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.symlink_to(REPO_ROOT, target_is_directory=True)


def ignore_for_copy(_src: str, names: list[str]) -> set[str]:
    ignored = {".git", ".secrets", "__pycache__"}
    return ignored.intersection(names)


def install_copy(dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO_ROOT, dest, ignore=ignore_for_copy, dirs_exist_ok=False)


def write_next_steps(dest: Path, mode: str) -> None:
    print(f"Installed Asana skill to {dest} using {mode} mode.")
    print("Next steps:")
    print("1. Add your PAT to ASANA_ACCESS_TOKEN or ~/.codex/skills-data/asana/asana_pat.")
    print("2. Copy asana-context.example.json to ~/.codex/skills-data/asana/asana-context.json.")
    print("3. Verify with: python3 scripts/asana_api.py whoami")
    if mode == "symlink":
        print(f"4. Update later with: git -C {REPO_ROOT} pull")


def main() -> None:
    ensure_python()
    args = parse_args()
    dest = Path(args.dest).expanduser().resolve()

    if dest.exists() or dest.is_symlink():
        if dest.is_symlink() and dest.resolve() == REPO_ROOT.resolve():
            write_next_steps(dest, args.mode)
            return
        if not args.replace:
            raise SystemExit(
                f"{dest} already exists. Re-run with --replace to swap it out safely."
            )

        stash_dir = Path.home() / ".codex" / ".tmp" / "asana-skill-preserve"
        if stash_dir.exists():
            shutil.rmtree(stash_dir)
        stash_dir.mkdir(parents=True, exist_ok=True)
        preserve_local_files(dest, stash_dir)
        remove_existing(dest)
    else:
        stash_dir = None

    if args.mode == "symlink":
        install_symlink(dest)
    else:
        install_copy(dest)

    if stash_dir is not None:
        restore_local_files(stash_dir)
        shutil.rmtree(stash_dir, ignore_errors=True)

    write_next_steps(dest, args.mode)


if __name__ == "__main__":
    main()
