from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "install_skill.py"
SPEC = importlib.util.spec_from_file_location("install_skill", MODULE_PATH)
INSTALL_SKILL = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(INSTALL_SKILL)


class InstallSkillCompanionTests(unittest.TestCase):
    def test_companion_skill_sources_exist(self) -> None:
        for name, source in INSTALL_SKILL.COMPANION_SKILLS.items():
            self.assertTrue(source.exists(), name)
            self.assertTrue((source / "SKILL.md").exists(), name)

    def test_install_companion_skills_copy_installs_all_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill_root = Path(tempdir)
            installed = INSTALL_SKILL.install_companion_skills(skill_root, "copy")

            self.assertEqual(len(installed), len(INSTALL_SKILL.COMPANION_SKILLS))
            installed_names = {name for name, _dest, _resolved in installed}
            self.assertEqual(installed_names, set(INSTALL_SKILL.COMPANION_SKILLS))

            for name, dest, resolved in installed:
                self.assertEqual(dest.name, name)
                self.assertTrue(dest.exists(), name)
                self.assertTrue((dest / "SKILL.md").exists(), name)
                self.assertEqual(resolved, dest.resolve())

    def test_install_companion_skills_removes_legacy_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill_root = Path(tempdir)
            legacy_dest = skill_root / "asana-inbox-cleanup"
            legacy_dest.mkdir()
            (legacy_dest / "SKILL.md").write_text("legacy")

            INSTALL_SKILL.install_companion_skills(skill_root, "copy")

            self.assertFalse(legacy_dest.exists())
            self.assertTrue((skill_root / "asana-my-tasks-organizer" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
