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


class TaskPlacementTests(unittest.TestCase):
    def test_create_task_with_project_only_keeps_existing_single_call_behavior(self) -> None:
        args = argparse.Namespace(
            name="Regular project task",
            workspace=None,
            project="project-1",
            section=None,
            parent=None,
            assignee=None,
            notes=None,
            html_notes=None,
            due_on=None,
            due_at=None,
            custom_field=[],
            insert_before=None,
            insert_after=None,
            compact=True,
        )

        with patch.object(ASANA_API, "get_token", return_value="token"), patch.object(
            ASANA_API, "load_context", return_value={}
        ), patch.object(ASANA_API, "load_cache", return_value={}), patch.object(
            ASANA_API,
            "api_request",
            return_value={"data": {"gid": "task-new", "name": "Regular project task"}},
        ) as api_request, patch.object(
            ASANA_API, "print_json"
        ):
            ASANA_API.command_create_task(args)

        api_request.assert_called_once()
        self.assertEqual(api_request.call_args.kwargs["path_or_url"], "/tasks")

    def test_create_task_places_new_task_before_anchor_in_section(self) -> None:
        args = argparse.Namespace(
            name="Seed backlog item",
            workspace=None,
            project="project-1",
            section="section-1",
            parent=None,
            assignee=None,
            notes=None,
            html_notes=None,
            due_on=None,
            due_at=None,
            custom_field=[],
            insert_before="task-anchor",
            insert_after=None,
            compact=True,
        )
        calls: list[tuple[str, str, dict[str, object] | None]] = []

        def fake_api_request(*, method: str, path_or_url: str, json_body: dict[str, object] | None = None, **_: object) -> dict[str, object]:
            calls.append((method, path_or_url, json_body))
            if method == "POST" and path_or_url == "/tasks":
                return {"data": {"gid": "task-new", "name": "Seed backlog item", "permalink_url": "https://example.com/task-new"}}
            if method == "GET" and path_or_url == "/sections/section-1/tasks":
                return {"data": [{"gid": "task-anchor"}]}
            if method == "POST" and path_or_url == "/sections/section-1/addTask":
                return {"data": {"gid": "section-1"}}
            raise AssertionError(f"Unexpected call: {method} {path_or_url}")

        with patch.object(ASANA_API, "get_token", return_value="token"), patch.object(
            ASANA_API, "load_context", return_value={}
        ), patch.object(ASANA_API, "load_cache", return_value={}), patch.object(
            ASANA_API, "api_request", side_effect=fake_api_request
        ), patch.object(ASANA_API, "print_json"):
            payload = ASANA_API.command_create_task(args)

        self.assertEqual(payload["review_url"], "https://example.com/task-new")
        self.assertEqual(
            calls[-1],
            (
                "POST",
                "/sections/section-1/addTask",
                {"data": {"task": "task-new", "insert_before": "task-anchor"}},
            ),
        )

    def test_update_task_can_reposition_without_field_update(self) -> None:
        args = argparse.Namespace(
            task_gid="task-1",
            name=None,
            project=None,
            section="section-1",
            assignee=None,
            notes=None,
            html_notes=None,
            due_on=None,
            due_at=None,
            completed=None,
            custom_field=[],
            insert_before=None,
            insert_after="task-anchor",
            compact=True,
        )
        seen_calls: list[tuple[str, str]] = []

        def fake_api_request(*, method: str, path_or_url: str, **_: object) -> dict[str, object]:
            seen_calls.append((method, path_or_url))
            if method == "GET" and path_or_url == "/tasks/task-1":
                return {"data": {"gid": "task-1", "name": "Task", "permalink_url": "https://example.com/task-1"}}
            if method == "GET" and path_or_url == "/sections/section-1/tasks":
                return {"data": [{"gid": "task-anchor"}]}
            if method == "POST" and path_or_url == "/sections/section-1/addTask":
                return {"data": {"gid": "section-1"}}
            raise AssertionError(f"Unexpected call: {method} {path_or_url}")

        with patch.object(ASANA_API, "get_token", return_value="token"), patch.object(
            ASANA_API, "load_context", return_value={}
        ), patch.object(ASANA_API, "load_cache", return_value={}), patch.object(
            ASANA_API, "api_request", side_effect=fake_api_request
        ), patch.object(ASANA_API, "print_json"):
            payload = ASANA_API.command_update_task(args)

        self.assertEqual(payload["review_url"], "https://example.com/task-1")
        self.assertNotIn(("PUT", "/tasks/task-1"), seen_calls)
        self.assertIn(("POST", "/sections/section-1/addTask"), seen_calls)

    def test_insert_before_and_after_are_mutually_exclusive(self) -> None:
        args = argparse.Namespace(insert_before="task-a", insert_after="task-b")

        with self.assertRaises(SystemExit):
            ASANA_API.task_position_args(args)


if __name__ == "__main__":
    unittest.main()
