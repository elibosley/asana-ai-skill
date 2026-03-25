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


class DailyBriefingTests(unittest.TestCase):
    def test_done_like_execute_now_task_becomes_release_watch(self) -> None:
        task_result = {
            "name": "Containers start with random mac",
            "work_type": "bug",
            "active_ai_action": {"action": "ask_to_execute_now"},
            "manager_plan": {"execution_candidate": True},
            "linked_prs": [{"pr_number": "2585"}],
            "reasons": ["Project state: Unraid OS 7.3 :: Test"],
        }

        bucket = ASANA_API.daily_briefing_bucket_key(task_result)

        self.assertEqual(bucket, "release_watch")

    def test_goal_style_task_is_background_noise(self) -> None:
        task_result = {
            "name": "Update and close your goal(s)",
            "work_type": "implementation",
            "active_ai_action": {"action": "ask_to_execute_now"},
            "manager_plan": {"execution_candidate": False},
            "linked_prs": [],
            "reasons": [],
        }

        bucket = ASANA_API.daily_briefing_bucket_key(task_result)

        self.assertEqual(bucket, "background")

    def test_rendered_markdown_includes_task_links(self) -> None:
        payload = {
            "briefing_date": "March 24, 2026",
            "summary": {
                "open_task_count": 4,
                "execute_now_count": 0,
                "release_watch_count": 1,
                "needs_verification_count": 0,
                "needs_follow_up_count": 0,
                "ready_to_close_count": 0,
                "background_count": 0,
            },
            "buckets": {
                "execute_now": [],
                "release_watch": [
                    {
                        "name": "Containers start with random mac",
                        "url": "https://app.asana.com/1/2/3",
                        "current_section": "Recently assigned",
                        "project_state": "Unraid OS 7.3 :: Test",
                        "pr": "PR #2585",
                        "due_date": None,
                        "next_action": "Keep this visible until ship close-out.",
                    }
                ],
                "needs_verification": [],
                "needs_follow_up": [],
                "ready_to_close": [],
                "background": [],
            },
        }

        rendered = ASANA_API.render_daily_briefing_markdown(payload)

        self.assertIn("[Containers start with random mac](https://app.asana.com/1/2/3)", rendered)
        self.assertIn("**Release / Ship Watch**", rendered)


if __name__ == "__main__":
    unittest.main()
