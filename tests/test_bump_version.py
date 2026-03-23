from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "bump_version.py"
SPEC = importlib.util.spec_from_file_location("bump_version", MODULE_PATH)
BUMP_VERSION = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BUMP_VERSION)


class ReleasePartClassificationTests(unittest.TestCase):
    def test_release_metadata_only_defaults_to_micro(self) -> None:
        part, reasons = BUMP_VERSION.classify_release_part(
            {"VERSION", "CHANGELOG.md"},
            "",
        )

        self.assertEqual(part, "micro")
        self.assertIn("Only VERSION/CHANGELOG release metadata changed.", reasons)

    def test_docs_only_changes_default_to_micro(self) -> None:
        part, reasons = BUMP_VERSION.classify_release_part(
            {"README.md", "SKILL.md", "references/recipes.md"},
            "",
        )

        self.assertEqual(part, "micro")
        self.assertIn("Diff only changes docs, prompts, or release metadata.", reasons)

    def test_behavior_fix_without_new_cli_defaults_to_patch(self) -> None:
        diff_text = """diff --git a/scripts/asana_api.py b/scripts/asana_api.py
@@
-    old_value = 1
+    old_value = 2
"""
        part, reasons = BUMP_VERSION.classify_release_part(
            {"scripts/asana_api.py"},
            diff_text,
        )

        self.assertEqual(part, "patch")
        self.assertIn(
            "Diff changes shipped script behavior without adding new public CLI surface.",
            reasons,
        )

    def test_new_cli_surface_defaults_to_minor(self) -> None:
        diff_text = """diff --git a/scripts/asana_api.py b/scripts/asana_api.py
@@
+    close_out_sections_parser = subparsers.add_parser(
+    close_out_sections_parser.add_argument("--apply")
"""
        part, reasons = BUMP_VERSION.classify_release_part(
            {"scripts/asana_api.py", "tests/test_section_close_out.py"},
            diff_text,
        )

        self.assertEqual(part, "minor")
        self.assertTrue(any("public CLI subcommand" in reason for reason in reasons))

    def test_breaking_marker_defaults_to_major(self) -> None:
        part, reasons = BUMP_VERSION.classify_release_part(
            {"scripts/asana_api.py"},
            "+BREAKING CHANGE: remove old task command",
        )

        self.assertEqual(part, "major")
        self.assertTrue(any("breaking-change marker" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
