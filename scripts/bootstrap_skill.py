#!/usr/bin/env python3
"""
Bootstrap the Asana skill for AI-assisted, low-touch setup.

This script:
- verifies local prerequisites
- refreshes the repo when safe
- installs the skill into Codex, Claude Code, or both
- ensures shared local state exists
- auto-builds asana-context.json when an Asana token is already available
- otherwise seeds a starter context file from the example
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LOCAL_STATE_DIR = Path.home() / ".agent-skills" / "asana"
LEGACY_LOCAL_STATE_DIR = Path.home() / ".codex" / "skills-data" / "asana"
TOKEN_FILE = LOCAL_STATE_DIR / "asana_pat"
CONTEXT_FILE = LOCAL_STATE_DIR / "asana-context.json"
SAFE_REPO_ROOT = Path.home() / ".agent-skills" / "sources"
ACTIVE_PROJECT_ENV_VARS = (
    "CLAUDECODE_PROJECT_DIR",
    "CLAUDE_PROJECT_DIR",
    "CODEX_PROJECT_DIR",
    "PROJECT_DIR",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap the Asana skill")
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
        help="Install mode for the selected agent targets",
    )
    parser.add_argument(
        "--skip-update",
        action="store_true",
        help="Skip the repo update step",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip the final whoami verification call",
    )
    parser.add_argument(
        "--repo-dir",
        help=(
            "Preferred checkout directory for the Asana skill repo. "
            "Defaults to the active Claude/Codex project directory when available, "
            "otherwise ~/.agent-skills/sources/asana-ai-skill."
        ),
    )
    return parser.parse_args()


def ensure_python() -> None:
    if sys.version_info < (3, 9):
        raise SystemExit("Python 3.9+ is required.")


def ensure_git() -> None:
    if shutil.which("git") is None:
        raise SystemExit("git is required for bootstrap and auto-update.")


def run_command(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def run_helper(command: list[str], repo_root: Path) -> dict[str, object]:
    completed = run_command([sys.executable, str(repo_root / "scripts" / "asana_api.py"), *command])
    return json.loads(completed.stdout)


def repo_root_for(path: Path) -> Path | None:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    root = completed.stdout.strip()
    return Path(root) if root else None


def active_project_directory(
    *,
    cwd: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path | None:
    env = environ or os.environ
    for key in ACTIVE_PROJECT_ENV_VARS:
        value = env.get(key)
        if not value:
            continue
        candidate = Path(value).expanduser()
        if candidate.exists():
            return candidate

    candidate_cwd = (cwd or Path.cwd()).expanduser()
    if candidate_cwd.exists():
        return candidate_cwd
    return None


def default_repo_checkout_dir(
    current_repo: Path,
    *,
    cwd: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    active_dir = active_project_directory(cwd=cwd, environ=environ)
    if active_dir is None:
        return SAFE_REPO_ROOT / current_repo.name

    resolved_repo = current_repo.resolve()
    resolved_active = active_dir.resolve()
    if resolved_active == resolved_repo or resolved_active.is_relative_to(resolved_repo):
        return current_repo
    return active_dir / current_repo.name


def looks_like_skill_repo(path: Path) -> bool:
    return (path / "SKILL.md").exists() and (path / "scripts" / "bootstrap_skill.py").exists()


def clone_or_copy_repo(source_repo: Path, target_repo: Path) -> None:
    target_repo.parent.mkdir(parents=True, exist_ok=True)
    source_git_root = repo_root_for(source_repo)
    if source_git_root == source_repo and shutil.which("git") is not None:
        completed = subprocess.run(
            ["git", "clone", str(source_repo), str(target_repo)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            return
    shutil.copytree(source_repo, target_repo, dirs_exist_ok=False)


def prompt_for_repo_dir(default_repo_dir: Path) -> Path:
    print(
        "Choose where to keep the Asana skill checkout for future updates.\n"
        f"Press Enter to use: {default_repo_dir}"
    )
    response = input("Repo directory: ").strip()
    if not response:
        return default_repo_dir
    return Path(response).expanduser()


def prepare_repo_checkout(
    current_repo: Path,
    *,
    repo_dir: str | None = None,
    cwd: Path | None = None,
    environ: Mapping[str, str] | None = None,
    interactive: bool | None = None,
) -> Path:
    target_repo = (
        Path(repo_dir).expanduser()
        if repo_dir
        else default_repo_checkout_dir(current_repo, cwd=cwd, environ=environ)
    )
    if interactive is None:
        interactive = sys.stdin.isatty()
    if repo_dir is None and interactive and target_repo.resolve() != current_repo.resolve():
        target_repo = prompt_for_repo_dir(target_repo)

    if target_repo.resolve() == current_repo.resolve():
        return current_repo

    if target_repo.exists():
        if target_repo.is_file():
            raise SystemExit(f"Repo target {target_repo} is a file. Choose a directory instead.")
        if not any(target_repo.iterdir()):
            target_repo.rmdir()
        elif not looks_like_skill_repo(target_repo):
            raise SystemExit(
                f"Repo target {target_repo} already exists and does not look like an Asana skill checkout."
            )
        else:
            return target_repo

    clone_or_copy_repo(current_repo, target_repo)
    return target_repo


def token_exists() -> bool:
    if TOKEN_FILE.exists() and TOKEN_FILE.read_text().strip():
        return True
    return bool(os.environ.get("ASANA_ACCESS_TOKEN"))


def maybe_update_repo(skip_update: bool, repo_root: Path) -> None:
    if skip_update:
        return
    completed = run_command(
        [sys.executable, str(repo_root / "scripts" / "update_skill.py"), "--force", "--best-effort"],
        cwd=repo_root,
        check=True,
    )
    if completed.stdout.strip():
        print(completed.stdout.strip())


def install_skill(agent: str, mode: str, repo_root: Path) -> None:
    completed = run_command(
        [
            sys.executable,
            str(repo_root / "scripts" / "install_skill.py"),
            "--agent",
            agent,
            "--mode",
            mode,
            "--replace",
        ],
        cwd=repo_root,
        check=True,
    )
    if completed.stdout.strip():
        print(completed.stdout.strip())


def choose_workspace(workspaces: list[dict[str, object]]) -> dict[str, object] | None:
    if not workspaces:
        return None
    return workspaces[0]


def build_context_from_api(repo_root: Path) -> dict[str, object]:
    whoami = run_helper(["whoami"], repo_root)
    workspaces = run_helper(["workspaces"], repo_root)
    user = whoami.get("data", {})
    workspace_list = workspaces.get("data", [])
    if not isinstance(user, dict) or not isinstance(workspace_list, list):
        raise RuntimeError("Unexpected Asana API response while building local context.")

    chosen_workspace = choose_workspace(workspace_list)
    if not chosen_workspace:
        raise RuntimeError("No Asana workspace was available for this token.")

    workspace_gid = str(chosen_workspace["gid"])
    teams_response = run_helper(["teams", "--workspace", workspace_gid], repo_root)
    teams_list = teams_response.get("data", [])
    if not isinstance(teams_list, list):
        raise RuntimeError("Unexpected Asana team response while building local context.")

    teams = {
        str(team["gid"]): str(team["name"])
        for team in teams_list
        if isinstance(team, dict) and team.get("gid") and team.get("name")
    }

    context = {
        "user_gid": str(user.get("gid", "me")),
        "user_name": str(user.get("name", "")),
        "workspace_gid": workspace_gid,
        "workspace_name": str(chosen_workspace.get("name", "")),
        "teams": teams,
    }

    if teams:
        first_team_gid = next(iter(teams))
        context["team_gid"] = first_team_gid
        context["team_name"] = teams[first_team_gid]

    return context


def ensure_local_state() -> None:
    LOCAL_STATE_DIR.mkdir(parents=True, exist_ok=True)
    if LEGACY_LOCAL_STATE_DIR.exists():
        for filename in ("asana_pat", "asana-context.json"):
            legacy_file = LEGACY_LOCAL_STATE_DIR / filename
            target = LOCAL_STATE_DIR / filename
            if legacy_file.exists() and not target.exists():
                shutil.copy2(legacy_file, target)


def write_context_if_missing_or_refreshable(repo_root: Path) -> str:
    context_example_file = repo_root / "asana-context.example.json"
    if token_exists():
        context = build_context_from_api(repo_root)
        CONTEXT_FILE.write_text(json.dumps(context, indent=2, sort_keys=True))
        team_count = len(context.get("teams", {}))
        return (
            f"Wrote {CONTEXT_FILE} from Asana API data for workspace "
            f"{context.get('workspace_name', '<unknown>')} with {team_count} teams."
        )

    if not CONTEXT_FILE.exists():
        CONTEXT_FILE.write_text(context_example_file.read_text())
        return f"Created starter context file at {CONTEXT_FILE}."

    return f"Left existing context file in place at {CONTEXT_FILE}."


def maybe_verify(skip_verify: bool, repo_root: Path) -> str:
    if skip_verify:
        return "Skipped final verification."
    if not token_exists():
        return (
            "Skipped Asana verification because no token was found. "
            f"Add a PAT to {TOKEN_FILE} or ASANA_ACCESS_TOKEN, then rerun bootstrap."
        )

    whoami = run_helper(["whoami"], repo_root)
    user = whoami.get("data", {})
    if not isinstance(user, dict):
        raise RuntimeError("Unexpected Asana API response during verification.")
    name = user.get("name", "<unknown>")
    email = user.get("email", "<unknown>")
    return f"Verified Asana access for {name} ({email})."


def print_next_steps(repo_root: Path) -> None:
    repo_path = repo_root
    if token_exists():
        print("The skill is ready to use.")
        print(f"Future refreshes: python3 {repo_path}/scripts/update_skill.py --force")
        return

    print("One more step is needed before the skill can talk to Asana:")
    print(f"1. Save your PAT to {TOKEN_FILE} with file mode 600, or set ASANA_ACCESS_TOKEN.")
    print("2. Rerun bootstrap or ask your AI tool to finish setup and verify access.")


def main() -> int:
    args = parse_args()
    ensure_python()
    ensure_git()
    repo_root = prepare_repo_checkout(REPO_ROOT, repo_dir=args.repo_dir)
    if repo_root != REPO_ROOT:
        print(f"Using Asana skill checkout at {repo_root}")
    ensure_local_state()
    maybe_update_repo(args.skip_update, repo_root)
    install_skill(args.agent, args.mode, repo_root)
    print(write_context_if_missing_or_refreshable(repo_root))
    print(maybe_verify(args.skip_verify, repo_root))
    print_next_steps(repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
