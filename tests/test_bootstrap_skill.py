from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "bootstrap_skill.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_skill", MODULE_PATH)
BOOTSTRAP_SKILL = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BOOTSTRAP_SKILL)


class BootstrapSkillRepoDirTests(unittest.TestCase):
    def test_active_project_directory_prefers_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            project_dir = Path(tempdir) / "claude-project"
            fallback_cwd = Path(tempdir) / "cwd"
            project_dir.mkdir()
            fallback_cwd.mkdir()

            resolved = BOOTSTRAP_SKILL.active_project_directory(
                cwd=fallback_cwd,
                environ={"CLAUDE_PROJECT_DIR": str(project_dir)},
            )

            self.assertEqual(resolved, project_dir)

    def test_default_repo_checkout_dir_uses_safe_fallback_without_active_project(self) -> None:
        current_repo = Path("/tmp/asana-ai-skill")

        resolved = BOOTSTRAP_SKILL.default_repo_checkout_dir(
            current_repo,
            cwd=Path("/definitely/missing"),
            environ={},
        )

        self.assertEqual(resolved, BOOTSTRAP_SKILL.SAFE_REPO_ROOT / current_repo.name)

    def test_default_repo_checkout_dir_uses_active_project_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            current_repo = root / "downloads" / "asana-ai-skill"
            active_project = root / "workspace"
            current_repo.mkdir(parents=True)
            active_project.mkdir()

            resolved = BOOTSTRAP_SKILL.default_repo_checkout_dir(
                current_repo,
                cwd=active_project,
                environ={},
            )

            self.assertEqual(resolved, active_project / "asana-ai-skill")

    def test_prepare_repo_checkout_keeps_current_repo_when_cwd_is_inside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            current_repo = Path(tempdir) / "asana-ai-skill"
            nested_cwd = current_repo / "scripts"
            nested_cwd.mkdir(parents=True)

            resolved = BOOTSTRAP_SKILL.prepare_repo_checkout(
                current_repo,
                cwd=nested_cwd,
                environ={},
                interactive=False,
            )

            self.assertEqual(resolved, current_repo)

    def test_prepare_repo_checkout_copies_repo_when_target_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            current_repo = root / "downloaded" / "asana-ai-skill"
            target_repo = root / "workspace" / "asana-ai-skill"
            (current_repo / "scripts").mkdir(parents=True)
            (current_repo / "SKILL.md").write_text("skill")
            (current_repo / "scripts" / "bootstrap_skill.py").write_text("bootstrap")

            with mock.patch.object(BOOTSTRAP_SKILL, "repo_root_for", return_value=None):
                resolved = BOOTSTRAP_SKILL.prepare_repo_checkout(
                    current_repo,
                    repo_dir=str(target_repo),
                    interactive=False,
                )

            self.assertEqual(resolved, target_repo)
            self.assertTrue((target_repo / "SKILL.md").exists())
            self.assertTrue((target_repo / "scripts" / "bootstrap_skill.py").exists())


if __name__ == "__main__":
    unittest.main()
