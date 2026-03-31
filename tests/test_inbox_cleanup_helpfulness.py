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


def sample_task(
    *,
    name: str,
    notes: str = "",
    memberships: list[dict[str, object]] | None = None,
    followers: list[dict[str, str]] | None = None,
    due_on: str | None = None,
) -> dict[str, object]:
    return {
        "name": name,
        "notes": notes,
        "html_notes": "",
        "created_at": "2026-03-20T12:00:00Z",
        "modified_at": "2026-03-30T12:00:00Z",
        "due_on": due_on,
        "projects": [membership["project"] for membership in (memberships or []) if isinstance(membership, dict) and membership.get("project")],
        "memberships": memberships or [],
        "assignee_section": {"name": "Recently assigned"},
        "assignee": {"gid": "user-1", "name": "Eli"},
        "followers": followers if followers is not None else [{"gid": "user-1", "name": "Eli"}],
        "collaborators": [],
        "parent": None,
        "permalink_url": "https://app.asana.com/1/2/3",
    }


class InboxCleanupHelpfulnessTests(unittest.TestCase):
    def test_extract_github_pr_links_detects_inline_pr_reference(self) -> None:
        links = ASANA_API.extract_github_pr_links("Expose IPv6 myunraid cert routes [PR #2593]")

        self.assertEqual([{"url": "", "owner": "", "repo": "", "pr_number": "2593"}], links)

    def test_verification_task_gets_specific_task_read_and_question(self) -> None:
        task = sample_task(
            name="Expose IPv6 myunraid cert routes [PR #2593]",
            memberships=[
                {
                    "project": {"gid": "project-1", "name": "Unraid OS 7.3"},
                    "section": {"gid": "section-1", "name": "Test"},
                }
            ],
        )
        task_context = {"task": task, "stories": []}

        classification = ASANA_API.classify_inbox_cleanup_task(
            task_context,
            datetime(2026, 3, 31, tzinfo=timezone.utc),
        )

        self.assertEqual(classification["category_key"], "needs_verification")
        self.assertEqual(classification["active_ai_action"]["action"], "ask_to_verify")
        self.assertIn("PR #2593", classification["manager_plan"]["task_read"])
        self.assertIn("verification", classification["manager_plan"]["task_read"].casefold())
        self.assertIn("verification pass", classification["manager_plan"]["ask_user"].casefold())

    def test_shared_decision_task_still_surfaces_execute_now(self) -> None:
        task = sample_task(
            name="Clarify CRA reporting vs retained documentation",
            notes="Need to define the reporting boundary and recommendation before implementation proceeds.",
            memberships=[
                {
                    "project": {"gid": "project-1", "name": "Cyber Resilience Act (CRA) Readiness"},
                    "section": {"gid": "section-1", "name": "Priority 1 - Decide Now"},
                }
            ],
            followers=[
                {"gid": "user-1", "name": "Eli"},
                {"gid": "user-2", "name": "Spencer"},
            ],
        )
        task_context = {"task": task, "stories": []}

        classification = ASANA_API.classify_inbox_cleanup_task(
            task_context,
            datetime(2026, 3, 31, tzinfo=timezone.utc),
        )

        self.assertFalse(classification["manager_comment_allowed"])
        self.assertEqual(classification["active_ai_action"]["action"], "ask_to_execute_now")
        self.assertIn("decision", classification["manager_plan"]["task_read"].casefold())
        self.assertIn("recommendation", classification["manager_plan"]["next_action"].casefold())
        self.assertIn("draft the recommendation", classification["manager_plan"]["ask_user"].casefold())


if __name__ == "__main__":
    unittest.main()
