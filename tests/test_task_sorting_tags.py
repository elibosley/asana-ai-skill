from __future__ import annotations

import argparse
import importlib.util
import socket
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib import error


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "asana_api.py"
SPEC = importlib.util.spec_from_file_location("asana_api", MODULE_PATH)
ASANA_API = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ASANA_API)


class _FakeResponse:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return self.payload.encode("utf-8")


class TaskSortingTagTests(unittest.TestCase):
    def test_add_task_tag_accepts_exact_tag_name(self) -> None:
        args = argparse.Namespace(
            task_gid="task-1",
            tag_gid="Deep Work",
            workspace="workspace-1",
            compact=True,
        )
        cache = ASANA_API.empty_cache()
        ASANA_API.cache_record(
            cache,
            "tags",
            ASANA_API.tag_cache_record(
                {"gid": "tag-deep", "name": "Deep Work", "color": "blue"},
                workspace_gid="workspace-1",
            ),
        )

        with patch.object(ASANA_API, "get_token", return_value="token"), patch.object(
            ASANA_API, "load_context", return_value={}
        ), patch.object(ASANA_API, "load_cache", return_value=cache), patch.object(
            ASANA_API, "post_task_relationship", return_value={"ok": True}
        ) as post_task_relationship:
            ASANA_API.command_add_task_tag(args)

        post_task_relationship.assert_called_once_with(
            args,
            "/tasks/task-1/addTag",
            {"tag": "tag-deep"},
        )

    def test_set_task_sorting_tag_removes_old_sorter_and_preserves_other_tags(self) -> None:
        args = argparse.Namespace(
            task_gid="task-1",
            sorting_tag="Deep Work",
            sorting_label=None,
            workspace="workspace-1",
            compact=True,
        )
        cache = ASANA_API.empty_cache()
        for gid, name in (
            ("tag-quick", "Quick Win"),
            ("tag-delegate", "Delegate"),
            ("tag-close", "Close Out"),
            ("tag-deep", "Deep Work"),
            ("tag-waiting", "Waiting"),
            ("tag-clarity", "Needs Clarity"),
        ):
            ASANA_API.cache_record(
                cache,
                "tags",
                ASANA_API.tag_cache_record({"gid": gid, "name": name}, workspace_gid="workspace-1"),
            )

        current_tags = [
            {"gid": "tag-quick", "name": "Quick Win", "color": "orange"},
            {"gid": "tag-project", "name": "Customer Escalation", "color": "red"},
        ]

        with patch.object(ASANA_API, "get_token", return_value="token"), patch.object(
            ASANA_API, "load_context", return_value={}
        ), patch.object(ASANA_API, "load_cache", return_value=cache), patch.object(
            ASANA_API, "get_task_tags", return_value=current_tags
        ), patch.object(ASANA_API, "print_json"), patch.object(
            ASANA_API, "api_request", return_value={"data": {}}
        ) as api_request:
            payload = ASANA_API.command_set_task_sorting_tag(args)

        self.assertEqual(payload["status"], "updated")
        self.assertTrue(payload["added_sorting_tag"])
        self.assertEqual(payload["removed_sorting_tags"], [{"gid": "tag-quick", "name": "Quick Win", "color": "orange"}])
        self.assertEqual(payload["preserved_tags"], [{"gid": "tag-project", "name": "Customer Escalation", "color": "red"}])
        self.assertEqual(
            [item["name"] for item in payload["resulting_tags"]],
            ["Customer Escalation", "Deep Work"],
        )
        self.assertEqual(
            [call.kwargs["path_or_url"] for call in api_request.call_args_list],
            ["/tasks/task-1/removeTag", "/tasks/task-1/addTag"],
        )

    def test_api_request_retries_transient_dns_failure(self) -> None:
        dns_error = error.URLError(socket.gaierror(8, "nodename nor servname provided, or not known"))

        with patch.object(
            ASANA_API.request,
            "urlopen",
            side_effect=[dns_error, _FakeResponse('{"data": []}')],
        ) as urlopen, patch.object(ASANA_API.time, "sleep") as sleep:
            payload = ASANA_API.api_request(
                token="token",
                method="GET",
                path_or_url="/users/me",
            )

        self.assertEqual(payload, {"data": []})
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once()


if __name__ == "__main__":
    unittest.main()
