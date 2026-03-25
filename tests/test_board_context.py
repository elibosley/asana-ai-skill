from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "asana_api.py"
SPEC = importlib.util.spec_from_file_location("asana_api", MODULE_PATH)
ASANA_API = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ASANA_API)


class BoardContextTests(unittest.TestCase):
    def test_happy_path_with_mixed_tasks(self) -> None:
        now = datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone.utc)
        section_payloads = [
            {
                "gid": "sec1",
                "name": "To Do",
                "tasks": [
                    {
                        "gid": "t1",
                        "name": "Task A",
                        "completed": False,
                        "due_on": "2026-03-20",
                        "modified_at": "2026-03-24T10:00:00.000Z",
                        "assignee": {"gid": "u1", "name": "Alice"},
                        "custom_fields": [
                            {"gid": "cf1", "name": "Priority", "resource_subtype": "enum", "display_value": "High"},
                        ],
                    },
                    {
                        "gid": "t2",
                        "name": "Task B",
                        "completed": False,
                        "due_on": None,
                        "modified_at": "2026-02-01T10:00:00.000Z",
                        "assignee": None,
                        "custom_fields": [
                            {"gid": "cf1", "name": "Priority", "resource_subtype": "enum", "display_value": None},
                        ],
                    },
                ],
            },
            {
                "gid": "sec2",
                "name": "Done",
                "tasks": [
                    {
                        "gid": "t3",
                        "name": "Task C",
                        "completed": True,
                        "due_on": "2026-03-15",
                        "modified_at": "2026-03-15T10:00:00.000Z",
                        "assignee": {"gid": "u1", "name": "Alice"},
                        "custom_fields": [
                            {"gid": "cf1", "name": "Priority", "resource_subtype": "enum", "display_value": "Low"},
                        ],
                    },
                ],
            },
        ]

        result = ASANA_API.compute_board_context(section_payloads, now)

        # Project summary
        self.assertEqual(result["project_summary"]["total_tasks"], 3)
        self.assertEqual(result["project_summary"]["completed_tasks"], 1)
        self.assertEqual(result["project_summary"]["incomplete_tasks"], 2)
        self.assertEqual(len(result["project_summary"]["sections"]), 2)
        self.assertEqual(result["project_summary"]["sections"][0]["total"], 2)
        self.assertEqual(result["project_summary"]["sections"][1]["completed"], 1)

        # Custom field coverage: cf1 filled in 2/3 tasks
        fields = result["custom_field_coverage"]["fields"]
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["filled_count"], 2)
        self.assertEqual(fields[0]["total_applicable"], 3)

        # Date coverage: 2 with due date, 1 without, 1 overdue (Task A is overdue)
        self.assertEqual(result["date_coverage"]["with_due_date"], 2)
        self.assertEqual(result["date_coverage"]["without_due_date"], 1)
        self.assertEqual(result["date_coverage"]["overdue"], 1)

        # Assignee distribution
        self.assertEqual(result["assignee_distribution"]["assigned"], 2)
        self.assertEqual(result["assignee_distribution"]["unassigned"], 1)

        # Staleness: t1 within 7d, t3 8-14d, t2 over 30d
        self.assertEqual(result["staleness"]["modified_within_7d"], 1)
        self.assertEqual(result["staleness"]["modified_8_to_14d"], 1)
        self.assertEqual(result["staleness"]["modified_over_30d"], 1)
        self.assertIsNotNone(result["staleness"]["oldest_stale_task"])
        self.assertEqual(result["staleness"]["oldest_stale_task"]["gid"], "t2")

    def test_empty_project(self) -> None:
        now = datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone.utc)
        section_payloads = [
            {"gid": "sec1", "name": "Backlog", "tasks": []},
        ]

        result = ASANA_API.compute_board_context(section_payloads, now)

        self.assertEqual(result["project_summary"]["total_tasks"], 0)
        self.assertEqual(result["project_summary"]["completed_tasks"], 0)
        self.assertEqual(result["date_coverage"]["coverage_pct"], 0.0)
        self.assertEqual(result["assignee_distribution"]["assigned"], 0)
        self.assertEqual(result["assignee_distribution"]["unassigned"], 0)
        self.assertEqual(result["staleness"]["oldest_stale_task"], None)
        self.assertEqual(result["custom_field_coverage"]["fields"], [])

    def test_no_custom_fields(self) -> None:
        now = datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone.utc)
        section_payloads = [
            {
                "gid": "sec1",
                "name": "To Do",
                "tasks": [
                    {
                        "gid": "t1",
                        "name": "Simple task",
                        "completed": False,
                        "due_on": "2026-04-01",
                        "modified_at": "2026-03-24T10:00:00.000Z",
                        "assignee": {"gid": "u1", "name": "Bob"},
                    },
                ],
            },
        ]

        result = ASANA_API.compute_board_context(section_payloads, now)

        self.assertEqual(result["custom_field_coverage"]["fields"], [])
        self.assertEqual(result["project_summary"]["total_tasks"], 1)
        self.assertEqual(result["date_coverage"]["with_due_date"], 1)
        self.assertEqual(result["date_coverage"]["overdue"], 0)


if __name__ == "__main__":
    unittest.main()
