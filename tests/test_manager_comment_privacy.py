from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "asana_api.py"
SPEC = importlib.util.spec_from_file_location("asana_api", MODULE_PATH)
ASANA_API = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ASANA_API)


class ManagerCommentPrivacyTests(unittest.TestCase):
    def test_private_task_with_only_assignee_activity_is_not_shared(self) -> None:
        task = {
            "assignee": {"gid": "user-1", "name": "Eli"},
            "followers": [{"gid": "user-1", "name": "Eli"}],
            "collaborators": [],
            "projects": [],
            "memberships": [],
            "parent": None,
        }
        stories = [
            {
                "type": "comment",
                "created_by": {"gid": "user-1", "name": "Eli"},
                "text": "My own note",
            }
        ]

        shared, reason = ASANA_API.task_is_shared_for_manager_comments(task, stories)

        self.assertFalse(shared)
        self.assertIsNone(reason)

    def test_task_with_non_assignee_commenter_is_shared(self) -> None:
        task = {
            "assignee": {"gid": "user-1", "name": "Eli"},
            "followers": [{"gid": "user-1", "name": "Eli"}],
            "collaborators": [],
            "projects": [],
            "memberships": [],
            "parent": None,
        }
        stories = [
            {
                "type": "comment",
                "created_by": {"gid": "user-2", "name": "Tiffany"},
                "text": "Looks good to me",
            }
        ]

        shared, reason = ASANA_API.task_is_shared_for_manager_comments(task, stories)

        self.assertTrue(shared)
        self.assertEqual(reason, "Task has comment history from other people, so it is treated as shared.")

    def test_task_with_non_assignee_follower_is_shared(self) -> None:
        task = {
            "assignee": {"gid": "user-1", "name": "Eli"},
            "followers": [
                {"gid": "user-1", "name": "Eli"},
                {"gid": "user-2", "name": "Spencer"},
            ],
            "collaborators": [],
            "projects": [],
            "memberships": [],
            "parent": None,
        }

        shared, reason = ASANA_API.task_is_shared_for_manager_comments(task, [])

        self.assertTrue(shared)
        self.assertEqual(reason, "Task has followers other than the assignee, so it is treated as shared.")

    def test_task_with_project_context_is_shared_even_without_other_people(self) -> None:
        task = {
            "assignee": {"gid": "user-1", "name": "Eli"},
            "followers": [{"gid": "user-1", "name": "Eli"}],
            "collaborators": [],
            "projects": [{"gid": "project-1", "name": "Shared Project"}],
            "memberships": [{"project": {"gid": "project-1", "name": "Shared Project"}, "section": {"gid": "section-1", "name": "Todo"}}],
            "parent": None,
        }

        shared, reason = ASANA_API.task_is_shared_for_manager_comments(task, [])

        self.assertTrue(shared)
        self.assertEqual(reason, "Task belongs to a project/section that is likely shared with others.")


if __name__ == "__main__":
    unittest.main()
