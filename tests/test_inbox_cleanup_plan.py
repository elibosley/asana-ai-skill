from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "asana_api.py"
SPEC = importlib.util.spec_from_file_location("asana_api", MODULE_PATH)
ASANA_API = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ASANA_API)


class InboxCleanupPlanTests(unittest.TestCase):
    def test_snapshot_payload_includes_plan_template_and_writes_files(self) -> None:
        snapshot_result = {
            "workspace_gid": "workspace-1",
            "my_tasks": {"gid": "mytasks-1", "name": "My Tasks"},
            "source_sections": ["Recently assigned"],
            "all_open": True,
            "review_sections": {"Review: Needs Next Action": {"gid": "section-review"}},
            "skill_advertising": {"my_tasks": {"section_counts": {"Recently assigned": 2, "Review: Needs Next Action": 1}}},
            "counts": {"all_open_tasks_in_my_tasks": 2},
            "tasks": [
                {
                    "task_gid": "task-1",
                    "name": "Clarify CRA reporting",
                    "permalink_url": "https://app.asana.com/1/2/3",
                    "current_section": "Recently assigned",
                    "target_section": "Review: Needs Next Action",
                    "category_key": "needs_next_action",
                    "reasons": ["Project state: CRA :: Decide"],
                    "linked_prs": [],
                    "task_read": "This is a scoping or decision task.",
                    "classification_basis": "The task still needs a concrete recommendation.",
                    "ask_user": "Do you want me to draft the recommendation now?",
                    "ai_help_summary": "I can draft the recommendation.",
                    "active_ai_action": {"action": "ask_to_execute_now"},
                    "manager_plan": {"next_action": "Write the recommendation."},
                }
            ],
        }
        args = argparse.Namespace(
            workspace=None,
            source_section=["Recently assigned"],
            all_open=True,
            max_tasks=0,
            no_paginate=False,
            limit_pages=0,
            compact=True,
            token="fake-token",
            snapshot_file=None,
            plan_template_file=None,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            args.snapshot_file = str(Path(tempdir) / "snapshot.json")
            args.plan_template_file = str(Path(tempdir) / "plan-template.json")
            with patch.object(ASANA_API, "build_inbox_cleanup_review_payload", return_value=snapshot_result):
                payload = ASANA_API.build_inbox_cleanup_snapshot_payload(args)

            self.assertEqual(payload["workflow"], ASANA_API.INBOX_CLEANUP_SNAPSHOT_WORKFLOW)
            self.assertIn("plan_template", payload)
            self.assertEqual(payload["tasks"][0]["task_read_hint"], "This is a scoping or decision task.")
            self.assertTrue(Path(payload["snapshot_file"]).exists())
            self.assertTrue(Path(payload["plan_template_file"]).exists())
            template = json.loads(Path(payload["plan_template_file"]).read_text())
            self.assertEqual(template["workflow"], ASANA_API.INBOX_CLEANUP_PLAN_WORKFLOW)
            self.assertEqual(template["tasks"][0]["decision"], "ask_user")

    def test_plan_preview_leaves_low_confidence_and_questions_unmoved(self) -> None:
        plan = {
            "workflow": ASANA_API.INBOX_CLEANUP_PLAN_WORKFLOW,
            "version": ASANA_API.INBOX_CLEANUP_PLAN_VERSION,
            "categories": [
                {"slug": "execute-now", "name": "Execute Now", "section_name": "WIP"},
                {"slug": "needs-user-input", "name": "Needs User Input", "section_name": ""},
            ],
            "tasks": [
                {
                    "task_gid": "task-1",
                    "decision": "bucket",
                    "category_slug": "execute-now",
                    "confidence": "high",
                    "why": "Active work.",
                    "question": "",
                },
                {
                    "task_gid": "task-2",
                    "decision": "ask_user",
                    "category_slug": "",
                    "confidence": "low",
                    "why": "Need Eli to decide the direction.",
                    "question": "Should this become active now?",
                },
                {
                    "task_gid": "task-3",
                    "decision": "bucket",
                    "category_slug": "execute-now",
                    "confidence": "low",
                    "why": "Probably active, but not certain.",
                    "question": "Should this really be WIP?",
                },
            ],
        }
        args = argparse.Namespace(
            workspace=None,
            no_paginate=False,
            limit_pages=0,
            token="fake-token",
            plan_file="unused",
            apply=False,
            include_low_confidence=False,
        )

        def fake_my_tasks_project(_: str, __: str) -> dict[str, str]:
            return {"gid": "mytasks-1", "name": "My Tasks"}

        def fake_my_tasks_tasks(*_: object, **__: object) -> list[dict[str, object]]:
            return [
                {"gid": "task-1", "name": "Task One", "assignee_section": {"name": "Recently assigned"}},
                {"gid": "task-2", "name": "Task Two", "assignee_section": {"name": "Recently assigned"}},
                {"gid": "task-3", "name": "Task Three", "assignee_section": {"name": "To Action Soon"}},
            ]

        with patch.object(ASANA_API, "load_json_file", return_value=plan), patch.object(
            ASANA_API, "workspace_default", return_value="workspace-1"
        ), patch.object(ASANA_API, "my_tasks_project", side_effect=fake_my_tasks_project), patch.object(
            ASANA_API, "my_tasks_tasks", side_effect=fake_my_tasks_tasks
        ), patch.object(ASANA_API, "my_tasks_sections", return_value=[{"gid": "section-wip", "name": "WIP"}]):
            payload = ASANA_API.build_inbox_cleanup_plan_payload(args)

        self.assertEqual(payload["mode"], "preview_plan")
        self.assertEqual(payload["counts"]["planned_moves"], 1)
        self.assertEqual(payload["counts"]["ask_user"], 1)
        self.assertEqual(payload["counts"]["low_confidence_requires_user"], 1)
        self.assertEqual(payload["results"][0]["target_section"], "WIP")
        self.assertEqual(payload["user_questions"][0]["task_gid"], "task-2")


if __name__ == "__main__":
    unittest.main()
