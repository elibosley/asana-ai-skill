from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "generate_cli_docs.py"
SPEC = importlib.util.spec_from_file_location("generate_cli_docs", MODULE_PATH)
GENERATE_CLI_DOCS = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(GENERATE_CLI_DOCS)


class CliReferenceGenerationTests(unittest.TestCase):
    def test_task_bundle_payload_matches_parser_surface(self) -> None:
        payload = GENERATE_CLI_DOCS.build_reference_payload()
        command = next(item for item in payload["commands"] if item["name"] == "task-bundle")

        self.assertEqual(
            [positional["dest"] for positional in command["positionals"]],
            ["task_gids"],
        )
        self.assertEqual(
            [option["dest"] for option in command["options"]],
            [
                "project_gid",
                "task_opt_fields",
                "story_opt_fields",
                "attachment_opt_fields",
            ],
        )
        self.assertTrue(command["includes_shared_options"])

    def test_shared_options_extract_common_compact_flag(self) -> None:
        payload = GENERATE_CLI_DOCS.build_reference_payload()
        shared_option_dests = [option["dest"] for option in payload["shared_options"]]
        self.assertEqual(shared_option_dests, ["compact"])

    def test_committed_reference_files_are_in_sync(self) -> None:
        payload = GENERATE_CLI_DOCS.build_reference_payload()
        expected_markdown = GENERATE_CLI_DOCS.render_markdown(payload)
        expected_json = GENERATE_CLI_DOCS.render_json(payload)

        self.assertEqual(
            (REPO_ROOT / "references" / "cli-reference.md").read_text(),
            expected_markdown,
        )
        self.assertEqual(
            (REPO_ROOT / "references" / "cli-reference.json").read_text(),
            expected_json,
        )


if __name__ == "__main__":
    unittest.main()
