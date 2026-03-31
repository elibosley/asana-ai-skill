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


class BulkLookupTests(unittest.TestCase):
    def test_command_task_uses_batch_for_multiple_gids(self) -> None:
        args = argparse.Namespace(
            task_gids=["task-1", "task-2"],
            opt_fields=None,
            compact=True,
        )
        batch_items = [
            {"status_code": 200, "body": {"data": {"gid": "task-1", "name": "One"}}},
            {"status_code": 200, "body": {"data": {"gid": "task-2", "name": "Two"}}},
        ]

        with patch.object(ASANA_API, "get_token", return_value="fake-token"), patch.object(
            ASANA_API, "batch_actions_request_chunked", return_value=batch_items
        ) as mock_batch:
            payload = ASANA_API.command_task(args)

        self.assertEqual(payload["command"], "task")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["items"][0]["requested_gid"], "task-1")
        self.assertEqual(payload["items"][1]["result"]["data"]["name"], "Two")
        self.assertEqual(mock_batch.call_count, 1)

    def test_command_task_status_bulk_dedupes_project_section_lookups(self) -> None:
        args = argparse.Namespace(
            task_gids=["task-1", "task-2"],
            project="project-1",
            include_task_position=False,
            opt_fields=None,
            compact=True,
        )
        batch_items = [
            {
                "status_code": 200,
                "body": {
                    "data": {
                        "gid": "task-1",
                        "name": "One",
                        "completed": False,
                        "memberships": [
                            {
                                "project": {"gid": "project-1", "name": "Project One"},
                                "section": {"gid": "section-1", "name": "Todo"},
                            }
                        ],
                        "custom_fields": [],
                    }
                },
            },
            {
                "status_code": 200,
                "body": {
                    "data": {
                        "gid": "task-2",
                        "name": "Two",
                        "completed": True,
                        "memberships": [
                            {
                                "project": {"gid": "project-1", "name": "Project One"},
                                "section": {"gid": "section-2", "name": "Doing"},
                            }
                        ],
                        "custom_fields": [],
                    }
                },
            },
        ]

        with patch.object(ASANA_API, "get_token", return_value="fake-token"), patch.object(
            ASANA_API, "batch_actions_request_chunked", return_value=batch_items
        ), patch.object(
            ASANA_API,
            "section_order_map",
            return_value=(
                [{"gid": "section-1"}, {"gid": "section-2"}],
                {"section-1": 1, "section-2": 2},
            ),
        ) as mock_section_order:
            payload = ASANA_API.command_task_status(args)

        self.assertEqual(payload["command"], "task-status")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["items"][0]["result"]["memberships"][0]["section_position"], 1)
        self.assertEqual(payload["items"][1]["result"]["memberships"][0]["section_position"], 2)
        self.assertEqual(mock_section_order.call_count, 1)

    def test_command_task_comments_bulk_filters_comment_stories(self) -> None:
        args = argparse.Namespace(
            task_gids=["task-1", "task-2"],
            opt_fields=None,
            paginate=False,
            limit_pages=0,
            compact=True,
        )
        batch_items = [
            {
                "status_code": 200,
                "body": {
                    "data": [
                        {"resource_subtype": "comment_added", "text": "Comment 1"},
                        {"resource_subtype": "assigned", "text": "System event"},
                    ]
                },
            },
            {
                "status_code": 200,
                "body": {
                    "data": [
                        {"type": "comment", "text": "Comment 2"},
                    ]
                },
            },
        ]

        with patch.object(ASANA_API, "get_token", return_value="fake-token"), patch.object(
            ASANA_API, "batch_actions_request_chunked", return_value=batch_items
        ):
            payload = ASANA_API.command_task_comments(args)

        self.assertEqual(payload["command"], "task-comments")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["items"][0]["result"]["comment_count"], 1)
        self.assertEqual(payload["items"][1]["result"]["data"][0]["text"], "Comment 2")


if __name__ == "__main__":
    unittest.main()
