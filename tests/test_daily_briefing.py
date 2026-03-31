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


class DailyBriefingPlanTests(unittest.TestCase):
    def test_snapshot_payload_includes_plan_template_and_writes_files(self) -> None:
        args = argparse.Namespace(
            workspace=None,
            max_tasks=0,
            no_paginate=False,
            limit_pages=0,
            compact=True,
            token="fake-token",
            snapshot_file=None,
            plan_template_file=None,
        )

        all_tasks = [
            {"gid": "task-1", "name": "Task One"},
        ]
        task_context = {
            "task": {
                "gid": "task-1",
                "name": "Verify PR #2593 on staging",
                "permalink_url": "https://app.asana.com/1/2/3",
                "assignee_section": {"name": "Recently assigned"},
                "due_on": "2026-03-31",
                "memberships": [
                    {
                        "project": {"name": "Unraid OS 7.3"},
                        "section": {"name": "Test"},
                    }
                ],
                "projects": [{"name": "Unraid OS 7.3"}],
                "followers": [{"gid": "user-1"}],
                "collaborators": [],
                "notes": "Validate the staging rollout before closing.",
            },
            "stories": [
                {
                    "resource_subtype": "comment_added",
                    "text": "Please test the latest build from PR #2593.",
                    "created_at": "2026-03-30T10:00:00Z",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tempdir:
            args.snapshot_file = str(Path(tempdir) / "daily-snapshot.json")
            args.plan_template_file = str(Path(tempdir) / "daily-plan-template.json")
            with patch.object(ASANA_API, "workspace_default", return_value="workspace-1"), patch.object(
                ASANA_API, "my_tasks_project", return_value={"gid": "mytasks-1", "name": "My Tasks"}
            ), patch.object(ASANA_API, "my_tasks_tasks", return_value=all_tasks), patch.object(
                ASANA_API, "fetch_task_review_context", return_value={"task-1": task_context}
            ), patch.object(
                ASANA_API, "my_tasks_summary", return_value={"section_counts": {"Recently assigned": 1}}
            ):
                payload = ASANA_API.build_daily_briefing_snapshot_payload(args)

            self.assertEqual(payload["workflow"], ASANA_API.DAILY_BRIEFING_SNAPSHOT_WORKFLOW)
            self.assertIn("plan_template", payload)
            self.assertEqual(payload["tasks"][0]["primary_pr"], "PR #2593")
            self.assertTrue(Path(payload["snapshot_file"]).exists())
            self.assertTrue(Path(payload["plan_template_file"]).exists())
            template = json.loads(Path(payload["plan_template_file"]).read_text())
            self.assertEqual(template["workflow"], ASANA_API.DAILY_BRIEFING_PLAN_WORKFLOW)
            self.assertEqual(template["tasks"][0]["decision"], "omit")

    def test_plan_payload_renders_ai_authored_markdown(self) -> None:
        plan = {
            "workflow": ASANA_API.DAILY_BRIEFING_PLAN_WORKFLOW,
            "version": ASANA_API.DAILY_BRIEFING_PLAN_VERSION,
            "overview": "Three tasks look worth attention this morning.",
            "focus": "Finish validation and unblock external follow-ups before pulling in fresh build work.",
            "categories": [
                {"slug": "execute-now", "name": "Execute Now", "display_order": 1},
                {"slug": "needs-follow-up", "name": "Needs Follow-Up", "display_order": 2},
            ],
            "tasks": [
                {
                    "task_gid": "task-1",
                    "decision": "highlight",
                    "bucket_slug": "execute-now",
                    "confidence": "high",
                    "why": "The task has a concrete next step and active rollout context.",
                    "next_action": "Run the staging verification pass now.",
                    "question": "",
                },
                {
                    "task_gid": "task-2",
                    "decision": "ask_user",
                    "bucket_slug": "",
                    "confidence": "low",
                    "why": "It is unclear whether this should stay active this week.",
                    "next_action": "",
                    "question": "Do you still want this in the active morning queue?",
                },
                {
                    "task_gid": "task-3",
                    "decision": "omit",
                    "bucket_slug": "background",
                    "confidence": "high",
                    "why": "This is planning noise for today.",
                    "next_action": "",
                    "question": "",
                },
            ],
        }
        args = argparse.Namespace(
            workspace=None,
            no_paginate=False,
            limit_pages=0,
            token="fake-token",
            plan_file="unused",
        )

        all_tasks = [
            {"gid": "task-1", "name": "Task One"},
            {"gid": "task-2", "name": "Task Two"},
            {"gid": "task-3", "name": "Task Three"},
        ]
        task_contexts = {
            "task-1": {
                "task": {
                    "gid": "task-1",
                    "name": "Verify PR #2593 on staging",
                    "permalink_url": "https://app.asana.com/1/2/3",
                    "assignee_section": {"name": "Recently assigned"},
                    "due_on": "2026-03-31",
                    "memberships": [{"project": {"name": "Unraid OS 7.3"}, "section": {"name": "Test"}}],
                    "projects": [{"name": "Unraid OS 7.3"}],
                },
                "stories": [],
            },
            "task-2": {
                "task": {
                    "gid": "task-2",
                    "name": "Decide CRA customer communication",
                    "permalink_url": "https://app.asana.com/1/2/4",
                    "assignee_section": {"name": "Review: Needs Next Action"},
                    "memberships": [{"project": {"name": "CRA"}, "section": {"name": "Decision"}}],
                    "projects": [{"name": "CRA"}],
                },
                "stories": [],
            },
            "task-3": {
                "task": {
                    "gid": "task-3",
                    "name": "Update goals",
                    "permalink_url": "https://app.asana.com/1/2/5",
                    "assignee_section": {"name": "Admin / Travel / Reminders"},
                    "memberships": [],
                    "projects": [],
                },
                "stories": [],
            },
        }

        with patch.object(ASANA_API, "load_json_file", return_value=plan), patch.object(
            ASANA_API, "workspace_default", return_value="workspace-1"
        ), patch.object(ASANA_API, "my_tasks_project", return_value={"gid": "mytasks-1", "name": "My Tasks"}), patch.object(
            ASANA_API, "my_tasks_tasks", return_value=all_tasks
        ), patch.object(
            ASANA_API, "fetch_task_review_context", return_value=task_contexts
        ):
            payload = ASANA_API.build_daily_briefing_plan_payload(args)

        self.assertEqual(payload["mode"], "render_plan")
        self.assertEqual(payload["summary"]["highlighted_count"], 1)
        self.assertEqual(payload["summary"]["ask_user_count"], 1)
        self.assertIn("execute-now", payload["buckets"])
        self.assertEqual(payload["user_questions"][0]["task_gid"], "task-2")
        self.assertIn("[Verify PR #2593 on staging](https://app.asana.com/1/2/3)", payload["rendered_markdown"])
        self.assertIn("**Needs Your Input**", payload["rendered_markdown"])


if __name__ == "__main__":
    unittest.main()
