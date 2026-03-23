from __future__ import annotations

import argparse
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "asana_api.py"
SPEC = importlib.util.spec_from_file_location("asana_api", MODULE_PATH)
ASANA_API = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ASANA_API)


class SectionCloseOutTests(unittest.TestCase):
    def test_find_section_record_resolves_by_exact_name(self) -> None:
        sections = [
            {"gid": "1", "name": "Old Section"},
            {"gid": "2", "name": "Work Completed"},
        ]

        section = ASANA_API.find_section_record(sections, "work completed")

        self.assertEqual(section["gid"], "2")

    def test_preview_shows_remaining_tasks_after_selected_move_subset(self) -> None:
        args = argparse.Namespace(
            project_gid="project-1",
            section=["Old Section"],
            move_to="Work Completed",
            completed_mode="completed",
            limit_pages=0,
            apply=False,
            compact=True,
            token="fake-token",
        )

        def fake_api_request(*, path_or_url: str, **_: object) -> dict[str, object]:
            if path_or_url == "/projects/project-1/sections":
                return {
                    "data": [
                        {"gid": "section-old", "name": "Old Section", "project": {"gid": "project-1", "name": "My Tasks"}},
                        {"gid": "section-done", "name": "Work Completed", "project": {"gid": "project-1", "name": "My Tasks"}},
                    ]
                }
            if path_or_url == "/sections/section-old/tasks":
                return {
                    "data": [
                        {"gid": "task-1", "name": "Completed Task", "completed": True, "permalink_url": "https://example.com/task-1"},
                        {"gid": "task-2", "name": "Open Task", "completed": False, "permalink_url": "https://example.com/task-2"},
                    ]
                }
            raise AssertionError(f"Unexpected path: {path_or_url}")

        with patch.object(ASANA_API, "api_request", side_effect=fake_api_request), patch.object(
            ASANA_API, "print_json"
        ):
            payload = ASANA_API.command_close_out_sections(args)

        self.assertEqual(payload["moved_task_count"], 0)
        self.assertEqual(payload["deleted_section_count"], 0)
        self.assertEqual(payload["sections"][0]["selected_task_count"], 1)
        self.assertEqual(payload["sections"][0]["remaining_task_count_after_selected_moves"], 1)
        self.assertTrue(payload["sections"][0]["planned_actions"]["move_selected_tasks"])
        self.assertFalse(payload["sections"][0]["planned_actions"]["delete_after_move"])

    def test_apply_moves_selected_tasks_and_deletes_empty_section(self) -> None:
        args = argparse.Namespace(
            project_gid="project-1",
            section=["Old Section"],
            move_to="Work Completed",
            completed_mode="completed",
            limit_pages=0,
            apply=True,
            compact=True,
            token="fake-token",
        )
        seen_calls: list[tuple[str, str]] = []

        def fake_api_request(*, method: str, path_or_url: str, **kwargs: object) -> dict[str, object]:
            seen_calls.append((method, path_or_url))
            if method == "GET" and path_or_url == "/projects/project-1/sections":
                return {
                    "data": [
                        {"gid": "section-old", "name": "Old Section", "project": {"gid": "project-1", "name": "My Tasks"}},
                        {"gid": "section-done", "name": "Work Completed", "project": {"gid": "project-1", "name": "My Tasks"}},
                    ]
                }
            if method == "GET" and path_or_url == "/sections/section-old/tasks":
                query = kwargs.get("query") or {}
                if query.get("limit") == "1":
                    return {"data": []}
                return {
                    "data": [
                        {"gid": "task-1", "name": "Completed Task", "completed": True, "permalink_url": "https://example.com/task-1"},
                    ]
                }
            if method == "POST" and path_or_url == "/tasks/task-1/addProject":
                return {"data": {"gid": "task-1"}}
            if method == "DELETE" and path_or_url == "/sections/section-old":
                return {"data": {"gid": "section-old"}}
            raise AssertionError(f"Unexpected call: {method} {path_or_url}")

        with patch.object(ASANA_API, "api_request", side_effect=fake_api_request), patch.object(
            ASANA_API, "print_json"
        ):
            payload = ASANA_API.command_close_out_sections(args)

        self.assertEqual(payload["moved_task_count"], 1)
        self.assertEqual(payload["deleted_section_count"], 1)
        self.assertEqual(payload["sections"][0]["applied_actions"]["moved_task_count"], 1)
        self.assertTrue(payload["sections"][0]["applied_actions"]["deleted"])
        self.assertIn(("POST", "/tasks/task-1/addProject"), seen_calls)
        self.assertIn(("DELETE", "/sections/section-old"), seen_calls)


if __name__ == "__main__":
    unittest.main()
