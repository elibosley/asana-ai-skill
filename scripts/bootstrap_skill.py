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


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LOCAL_STATE_DIR = Path.home() / ".agent-skills" / "asana"
LEGACY_LOCAL_STATE_DIR = Path.home() / ".codex" / "skills-data" / "asana"
TOKEN_FILE = LOCAL_STATE_DIR / "asana_pat"
CONTEXT_FILE = LOCAL_STATE_DIR / "asana-context.json"
CONTEXT_EXAMPLE_FILE = REPO_ROOT / "asana-context.example.json"


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
    return parser.parse_args()


def ensure_python() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10+ is required.")


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


def run_helper(command: list[str]) -> dict[str, object]:
    completed = run_command([sys.executable, str(REPO_ROOT / "scripts" / "asana_api.py"), *command])
    return json.loads(completed.stdout)


def token_exists() -> bool:
    if TOKEN_FILE.exists() and TOKEN_FILE.read_text().strip():
        return True
    return bool(os.environ.get("ASANA_ACCESS_TOKEN"))


def maybe_update_repo(skip_update: bool) -> None:
    if skip_update:
        return
    completed = run_command(
        [sys.executable, str(REPO_ROOT / "scripts" / "update_skill.py"), "--force", "--best-effort"],
        cwd=REPO_ROOT,
        check=True,
    )
    if completed.stdout.strip():
        print(completed.stdout.strip())


def install_skill(agent: str, mode: str) -> None:
    completed = run_command(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "install_skill.py"),
            "--agent",
            agent,
            "--mode",
            mode,
            "--replace",
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    if completed.stdout.strip():
        print(completed.stdout.strip())


def choose_workspace(workspaces: list[dict[str, object]]) -> dict[str, object] | None:
    if not workspaces:
        return None
    return workspaces[0]


def build_context_from_api() -> dict[str, object]:
    whoami = run_helper(["whoami"])
    workspaces = run_helper(["workspaces"])
    user = whoami.get("data", {})
    workspace_list = workspaces.get("data", [])
    if not isinstance(user, dict) or not isinstance(workspace_list, list):
        raise RuntimeError("Unexpected Asana API response while building local context.")

    chosen_workspace = choose_workspace(workspace_list)
    if not chosen_workspace:
        raise RuntimeError("No Asana workspace was available for this token.")

    workspace_gid = str(chosen_workspace["gid"])
    teams_response = run_helper(["teams", "--workspace", workspace_gid])
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


def write_context_if_missing_or_refreshable() -> str:
    if token_exists():
        context = build_context_from_api()
        CONTEXT_FILE.write_text(json.dumps(context, indent=2, sort_keys=True))
        team_count = len(context.get("teams", {}))
        return (
            f"Wrote {CONTEXT_FILE} from Asana API data for workspace "
            f"{context.get('workspace_name', '<unknown>')} with {team_count} teams."
        )

    if not CONTEXT_FILE.exists():
        CONTEXT_FILE.write_text(CONTEXT_EXAMPLE_FILE.read_text())
        return f"Created starter context file at {CONTEXT_FILE}."

    return f"Left existing context file in place at {CONTEXT_FILE}."


def maybe_verify(skip_verify: bool) -> str:
    if skip_verify:
        return "Skipped final verification."
    if not token_exists():
        return (
            "Skipped Asana verification because no token was found. "
            f"Add a PAT to {TOKEN_FILE} or ASANA_ACCESS_TOKEN, then rerun bootstrap."
        )

    whoami = run_helper(["whoami"])
    user = whoami.get("data", {})
    if not isinstance(user, dict):
        raise RuntimeError("Unexpected Asana API response during verification.")
    name = user.get("name", "<unknown>")
    email = user.get("email", "<unknown>")
    return f"Verified Asana access for {name} ({email})."


def print_next_steps() -> None:
    repo_path = REPO_ROOT
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
    ensure_local_state()
    maybe_update_repo(args.skip_update)
    install_skill(args.agent, args.mode)
    print(write_context_if_missing_or_refreshable())
    print(maybe_verify(args.skip_verify))
    print_next_steps()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
