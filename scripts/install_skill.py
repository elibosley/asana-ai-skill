#!/usr/bin/env python3
"""
Install or update the Asana skill into Codex, Claude Code, or both.

Defaults to a symlink install so the paired updater can fast-forward the live skill.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_STATE_DIR = Path.home() / ".agent-skills" / "asana"
LEGACY_LOCAL_STATE_DIR = Path.home() / ".codex" / "skills-data" / "asana"
VERSION_FILE = REPO_ROOT / "VERSION"
DEFAULT_DESTS = {
    "codex": Path.home() / ".codex" / "skills" / "asana",
    "claude": Path.home() / ".claude" / "skills" / "asana",
}
ENTRYPOINT_ROOT = REPO_ROOT / "entrypoints"
COMPANION_SKILLS = {
    "asana-daily-briefing": ENTRYPOINT_ROOT / "asana-daily-briefing",
    "asana-inbox-cleanup": ENTRYPOINT_ROOT / "asana-inbox-cleanup",
    "asana-close-out-sections": ENTRYPOINT_ROOT / "asana-close-out-sections",
    "asana-project-working-set": ENTRYPOINT_ROOT / "asana-project-working-set",
    "asana-weekly-manager-summary": ENTRYPOINT_ROOT / "asana-weekly-manager-summary",
    "asana-friday-follow-up-summary": ENTRYPOINT_ROOT / "asana-friday-follow-up-summary",
}
PRESERVED_FILES = [
    (".secrets/asana_pat", False),
    ("asana-context.json", True),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the Asana skill locally")
    parser.add_argument(
        "--agent",
        choices=("codex", "claude", "both"),
        default="both",
        help="Install into Codex, Claude Code, or both",
    )
    parser.add_argument(
        "--mode",
        choices=("symlink", "copy"),
        default="symlink",
        help="Install as a symlink for easy updates, or copy files into place",
    )
    parser.add_argument(
        "--dest",
        help="Destination skill directory for a single-agent install",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing install and preserve local token/context files when possible",
    )
    return parser.parse_args()


def ensure_python() -> None:
    if sys.version_info < (3, 9):
        raise SystemExit("Python 3.9+ is required.")


def safe_resolve(path: Path) -> Path | None:
    try:
        return path.resolve()
    except OSError:
        return None


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
    if LEGACY_LOCAL_STATE_DIR.exists():
        LEGACY_LOCAL_STATE_DIR.mkdir(parents=True, exist_ok=True)


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


def install_companion(dest: Path, source: Path, mode: str) -> None:
    if dest.exists() or dest.is_symlink():
        remove_existing(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if mode == "symlink":
        dest.symlink_to(source, target_is_directory=True)
        return
    shutil.copytree(source, dest, ignore=ignore_for_copy, dirs_exist_ok=False)


def install_companion_skills(skill_root: Path, mode: str) -> list[tuple[str, Path, Path]]:
    installed: list[tuple[str, Path, Path]] = []
    for name, source in COMPANION_SKILLS.items():
        if not source.exists():
            raise SystemExit(f"Companion skill source is missing: {source}")
        if not (source / "SKILL.md").exists():
            raise SystemExit(f"Companion skill is missing SKILL.md: {source / 'SKILL.md'}")
        dest = skill_root / name
        install_companion(dest, source, mode)
        installed.append((name, dest, Path(os.path.realpath(dest))))
    return installed


def install_one(dest: Path, mode: str, replace: bool) -> tuple[Path, Path]:
    resolved_dest = safe_resolve(dest)

    if dest.exists() or dest.is_symlink():
        if dest.is_symlink() and resolved_dest == REPO_ROOT.resolve():
            return dest, Path(os.path.realpath(dest))
        if dest.exists() and not dest.is_symlink() and resolved_dest == REPO_ROOT.resolve():
            raise SystemExit(
                f"Refusing to install into the repo source path itself: {dest}"
            )
        if not replace:
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

    if mode == "symlink":
        install_symlink(dest)
    else:
        install_copy(dest)

    if stash_dir is not None:
        restore_local_files(stash_dir)
        shutil.rmtree(stash_dir, ignore_errors=True)

    return dest, Path(os.path.realpath(dest))


def selected_targets(agent: str, explicit_dest: str | None) -> list[tuple[str, Path]]:
    if explicit_dest:
        if agent == "both":
            raise SystemExit("--dest can only be used with --agent codex or --agent claude.")
        return [(agent, Path(explicit_dest).expanduser())]
    if agent == "both":
        return [("codex", DEFAULT_DESTS["codex"]), ("claude", DEFAULT_DESTS["claude"])]
    return [(agent, DEFAULT_DESTS[agent])]


def write_next_steps(installed: list[tuple[str, Path, Path]], mode: str) -> None:
    current_version = VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "unknown"
    for agent, install_path, source_path in installed:
        if install_path == source_path:
            print(f"Installed Asana skill for {agent} at {install_path} using {mode} mode.")
        else:
            print(
                f"Installed Asana skill for {agent} at {install_path} -> {source_path} "
                f"using {mode} mode."
            )
        companion_names = ", ".join(sorted(COMPANION_SKILLS))
        print(f"Workflow entrypoints installed for {agent}: {companion_names}")
    print(f"Current skill version: v{current_version}")
    print("Next steps:")
    print("1. Add your PAT to ASANA_ACCESS_TOKEN or ~/.agent-skills/asana/asana_pat.")
    print("2. Copy asana-context.example.json to ~/.agent-skills/asana/asana-context.json.")
    print("3. Verify with: python3 scripts/asana_api.py whoami")
    print("4. Auto-update with: python3 scripts/update_skill.py --force")
    if mode == "symlink":
        print(f"5. Manual git update still works: git -C {REPO_ROOT} pull --ff-only")


def main() -> None:
    ensure_python()
    args = parse_args()
    installed = []
    for agent, dest in selected_targets(args.agent, args.dest):
        install_path, source_path = install_one(dest, args.mode, args.replace)
        installed.append((agent, install_path, source_path))
        install_companion_skills(install_path.parent, args.mode)
    write_next_steps(installed, args.mode)


if __name__ == "__main__":
    main()
