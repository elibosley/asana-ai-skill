#!/usr/bin/env python3
"""
Thin Asana API helper for local AI agent skills.

Features:
- Reads PAT from ASANA_ACCESS_TOKEN or a local token file
- Reads default workspace/team IDs from a local context file when present
- Supports generic GET/POST/PUT/DELETE requests
- Supports JSON and multipart/form-data requests
- Includes convenience subcommands for common Asana flows
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import mimetypes
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from urllib import error, parse, request


BASE_URL = "https://app.asana.com/api/1.0"
SKILL_DIR = Path(__file__).resolve().parent.parent
LOCAL_STATE_DIR = Path.home() / ".agent-skills" / "asana"
LEGACY_LOCAL_STATE_DIR = Path.home() / ".codex" / "skills-data" / "asana"
DEFAULT_TOKEN_FILE = LOCAL_STATE_DIR / "asana_pat"
LEGACY_SHARED_TOKEN_FILE = LEGACY_LOCAL_STATE_DIR / "asana_pat"
LEGACY_TOKEN_FILE = SKILL_DIR / ".secrets" / "asana_pat"
DEFAULT_CONTEXT_FILE = LOCAL_STATE_DIR / "asana-context.json"
LEGACY_SHARED_CONTEXT_FILE = LEGACY_LOCAL_STATE_DIR / "asana-context.json"
LEGACY_CONTEXT_FILE = SKILL_DIR / "asana-context.json"
DEFAULT_CACHE_FILE = LOCAL_STATE_DIR / "asana-cache.json"
LEGACY_SHARED_CACHE_FILE = LEGACY_LOCAL_STATE_DIR / "asana-cache.json"
LEGACY_CACHE_FILE = SKILL_DIR / ".cache" / "asana-cache.json"


def token_file() -> Path:
    configured = os.environ.get("ASANA_TOKEN_FILE")
    if configured:
        return Path(configured).expanduser()
    if DEFAULT_TOKEN_FILE.exists():
        return DEFAULT_TOKEN_FILE
    if LEGACY_SHARED_TOKEN_FILE.exists():
        return LEGACY_SHARED_TOKEN_FILE
    return LEGACY_TOKEN_FILE


def context_file() -> Path:
    configured = os.environ.get("ASANA_CONTEXT_FILE")
    if configured:
        return Path(configured).expanduser()
    if DEFAULT_CONTEXT_FILE.exists():
        return DEFAULT_CONTEXT_FILE
    if LEGACY_SHARED_CONTEXT_FILE.exists():
        return LEGACY_SHARED_CONTEXT_FILE
    return LEGACY_CONTEXT_FILE


def cache_file() -> Path:
    configured = os.environ.get("ASANA_CACHE_FILE")
    if configured:
        return Path(configured).expanduser()
    if DEFAULT_CACHE_FILE.exists():
        return DEFAULT_CACHE_FILE
    if LEGACY_SHARED_CACHE_FILE.exists():
        return LEGACY_SHARED_CACHE_FILE
    if LEGACY_CACHE_FILE.exists():
        return LEGACY_CACHE_FILE
    return DEFAULT_CACHE_FILE


def load_context() -> dict[str, Any]:
    file_path = context_file()
    if not file_path.exists():
        return {}
    return json.loads(file_path.read_text())


def empty_cache() -> dict[str, Any]:
    return {
        "metadata": {"updated_at": None},
        "workspaces": {"by_gid": {}},
        "teams": {"by_gid": {}},
        "projects": {"by_gid": {}},
        "users": {"by_gid": {}},
        "tags": {"by_gid": {}},
    }


def ensure_cache_shape(cache: dict[str, Any]) -> dict[str, Any]:
    cache.setdefault("metadata", {})
    for bucket_name in ("workspaces", "teams", "projects", "users", "tags"):
        bucket = cache.setdefault(bucket_name, {})
        if not isinstance(bucket, dict):
            cache[bucket_name] = {"by_gid": {}}
            continue
        bucket.setdefault("by_gid", {})
        if not isinstance(bucket["by_gid"], dict):
            bucket["by_gid"] = {}
    return cache


def load_cache() -> dict[str, Any]:
    file_path = cache_file()
    if not file_path.exists():
        return empty_cache()
    return ensure_cache_shape(json.loads(file_path.read_text()))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso_timestamp(value: str | None) -> datetime:
    token = str(value or "").strip()
    if not token:
        return datetime.min.replace(tzinfo=timezone.utc)
    if token.endswith("Z"):
        token = f"{token[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(token)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def merge_cache_records(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if value is not None:
            merged[key] = value

    existing_cached_at = parse_iso_timestamp(existing.get("cached_at"))
    incoming_cached_at = parse_iso_timestamp(incoming.get("cached_at"))
    merged["cached_at"] = (
        incoming.get("cached_at")
        if incoming_cached_at >= existing_cached_at
        else existing.get("cached_at")
    )
    return merged


def merge_cache_data(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = ensure_cache_shape(dict(base))
    incoming_normalized = ensure_cache_shape(dict(incoming))

    for bucket_name in ("workspaces", "teams", "projects", "users", "tags"):
        merged_bucket = cache_bucket(merged, bucket_name)
        incoming_bucket = cache_bucket(incoming_normalized, bucket_name)
        for gid, record in incoming_bucket["by_gid"].items():
            if not isinstance(record, dict):
                continue
            existing_record = merged_bucket["by_gid"].get(gid, {})
            if isinstance(existing_record, dict):
                merged_bucket["by_gid"][gid] = merge_cache_records(existing_record, record)
            else:
                merged_bucket["by_gid"][gid] = dict(record)

    merged_metadata = merged.setdefault("metadata", {})
    incoming_metadata = incoming_normalized.get("metadata", {})
    for key in ("current_user_gid", "current_user_name"):
        if incoming_metadata.get(key) is not None:
            merged_metadata[key] = incoming_metadata[key]
    return merged


@contextlib.contextmanager
def cache_lock(file_path: Path):
    lock_path = file_path.with_name(f"{file_path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def save_cache(cache: dict[str, Any]) -> Path:
    file_path = cache_file()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with cache_lock(file_path):
        on_disk = empty_cache()
        if file_path.exists():
            on_disk = ensure_cache_shape(json.loads(file_path.read_text()))

        normalized = merge_cache_data(on_disk, cache)
        normalized["metadata"]["updated_at"] = now_iso()

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=file_path.parent,
            prefix=f"{file_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp_file:
            tmp_file.write(f"{json.dumps(normalized, indent=2, sort_keys=True)}\n")
            temp_path = Path(tmp_file.name)

        os.replace(temp_path, file_path)
    return file_path


def cache_bucket(cache: dict[str, Any], bucket_name: str) -> dict[str, Any]:
    return ensure_cache_shape(cache).setdefault(bucket_name, {"by_gid": {}})


def cache_record(cache: dict[str, Any], bucket_name: str, record: dict[str, Any]) -> None:
    gid = str(record.get("gid") or "").strip()
    if not gid:
        return
    bucket = cache_bucket(cache, bucket_name)
    existing = bucket["by_gid"].get(gid, {})
    merged = dict(existing)
    merged.update({key: value for key, value in record.items() if value is not None})
    merged["cached_at"] = now_iso()
    bucket["by_gid"][gid] = merged


def cache_records(cache: dict[str, Any], bucket_name: str, records: list[dict[str, Any]]) -> None:
    for record in records:
        if isinstance(record, dict):
            cache_record(cache, bucket_name, record)


def normalize_match_key(value: str | None) -> str:
    return str(value or "").strip().casefold()


def is_gid_like(value: str | None) -> bool:
    token = str(value or "").strip()
    return bool(token) and token.isdigit()


def find_cached_record(
    cache: dict[str, Any],
    bucket_name: str,
    identifier: str | None,
    *,
    fields: tuple[str, ...],
) -> dict[str, Any] | None:
    token = str(identifier or "").strip()
    if not token:
        return None
    if is_gid_like(token):
        return cache_bucket(cache, bucket_name)["by_gid"].get(token)

    lowered = normalize_match_key(token)
    matches: list[dict[str, Any]] = []
    for record in cache_bucket(cache, bucket_name)["by_gid"].values():
        if not isinstance(record, dict):
            continue
        if any(normalize_match_key(record.get(field)) == lowered for field in fields):
            matches.append(record)

    if not matches:
        return None
    unique_matches: dict[str, dict[str, Any]] = {}
    for record in matches:
        gid = str(record.get("gid") or "").strip()
        if gid:
            unique_matches[gid] = record
    if len(unique_matches) == 1:
        return next(iter(unique_matches.values()))
    match_list = ", ".join(
        f"{record.get('name', record.get('gid'))} ({record.get('gid')})"
        for record in unique_matches.values()
    )
    raise SystemExit(f"Ambiguous cached {bucket_name[:-1]} identifier '{token}': {match_list}")


def user_cache_record(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "gid": user.get("gid"),
        "name": user.get("name"),
        "email": user.get("email"),
    }


def workspace_cache_record(workspace: dict[str, Any]) -> dict[str, Any]:
    return {
        "gid": workspace.get("gid"),
        "name": workspace.get("name"),
    }


def team_cache_record(team: dict[str, Any], *, workspace_gid: str | None = None) -> dict[str, Any]:
    return {
        "gid": team.get("gid"),
        "name": team.get("name"),
        "workspace_gid": workspace_gid,
    }


def project_cache_record(project: dict[str, Any], *, team_gid: str | None = None) -> dict[str, Any]:
    team = project.get("team") if isinstance(project.get("team"), dict) else {}
    owner = project.get("owner") if isinstance(project.get("owner"), dict) else {}
    return {
        "gid": project.get("gid"),
        "name": project.get("name"),
        "team_gid": team.get("gid") or team_gid,
        "team_name": team.get("name"),
        "owner_gid": owner.get("gid"),
        "owner_name": owner.get("name"),
    }


def tag_cache_record(tag: dict[str, Any]) -> dict[str, Any]:
    return {
        "gid": tag.get("gid"),
        "name": tag.get("name"),
        "color": tag.get("color"),
    }


def get_token(args: argparse.Namespace) -> str:
    file_path = token_file()

    token = (
        getattr(args, "token", None)
        or os.environ.get("ASANA_ACCESS_TOKEN")
        or (file_path.read_text().strip() if file_path.exists() else "")
    )
    if not token:
        raise SystemExit(
            "Missing Asana token. Set ASANA_ACCESS_TOKEN or write the PAT to "
            f"{file_path}."
        )
    return token


def parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got: {value}")


def parse_kv(items: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        result[key] = value
    return result


def parse_many_gid(items: list[str] | None) -> list[str]:
    values: list[str] = []
    for item in items or []:
        for part in item.split(","):
            cleaned = part.strip()
            if cleaned:
                values.append(cleaned)
    return values


def nullable_arg(value: str | None) -> str | None:
    if value is None:
        return None
    if value.strip().lower() == "null":
        return None
    return value


def load_inline_or_file_value(
    inline_value: str | None,
    file_path: str | None,
    *,
    field_name: str,
) -> str | None:
    if inline_value is not None and file_path is not None:
        raise SystemExit(f"Pass only one of --{field_name} or --{field_name}-file")
    if file_path is None:
        return inline_value
    return Path(file_path).read_text()


AI_MESSAGE_HEADER_RE = re.compile(
    r"(?P<header><strong>\s*AI MESSAGE DISCLAIMER\s*</strong>)(?P<rest>.*)",
    flags=re.IGNORECASE | re.DOTALL,
)
AI_MESSAGE_LABEL_RE = re.compile(
    r"(<strong>\s*(?!AI MESSAGE DISCLAIMER\b)[^<]+?:\s*</strong>)(.*?)(?=(<strong>\s*(?!AI MESSAGE DISCLAIMER\b)[^<]+?:\s*</strong>)|$)",
    flags=re.IGNORECASE | re.DOTALL,
)
AI_MESSAGE_LABEL_ONLY_RE = re.compile(
    r"^(<strong>\s*(?!AI MESSAGE DISCLAIMER\b)[^<]+?:\s*</strong>)$",
    flags=re.IGNORECASE | re.DOTALL,
)
AI_MESSAGE_LABEL_WITH_CONTENT_RE = re.compile(
    r"^(<strong>\s*(?!AI MESSAGE DISCLAIMER\b)[^<]+?:\s*</strong>)(.+)$",
    flags=re.IGNORECASE | re.DOTALL,
)


def collapse_html_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def render_ai_message_sections(
    sections: list[tuple[str | None, str, str | list[str]]],
) -> str | None:
    if not sections:
        return None

    parts = ["<body><strong>AI MESSAGE DISCLAIMER</strong>"]
    for label_html, kind, content in sections:
        if label_html is None:
            scalar = collapse_html_whitespace(str(content))
            if scalar:
                parts.append(f"<blockquote>{scalar}</blockquote>")
            continue

        parts.append(label_html)
        if kind == "list":
            items = [
                f"<li>{collapse_html_whitespace(item)}</li>"
                for item in content
                if collapse_html_whitespace(item)
            ]
            if items:
                parts.append(f"<ul>{''.join(items)}</ul>")
            continue

        scalar = collapse_html_whitespace(str(content))
        if scalar:
            parts.append(f"<blockquote>{scalar}</blockquote>")

    parts.append("</body>")
    return "".join(parts)


def normalize_legacy_ai_message_list(inner: str) -> str | None:
    disclaimer_match = AI_MESSAGE_HEADER_RE.match(inner)
    if not disclaimer_match:
        return None

    rest = disclaimer_match.group("rest").strip()
    if re.search(r"<(ol|blockquote|pre)\b", rest, flags=re.IGNORECASE):
        return None

    ul_match = re.fullmatch(r"<ul\b[^>]*>(?P<items>.*)</ul>", rest, flags=re.IGNORECASE | re.DOTALL)
    if not ul_match:
        return None

    item_matches = re.findall(
        r"<li\b[^>]*>(.*?)</li>",
        ul_match.group("items"),
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not item_matches:
        return None

    sections: list[tuple[str | None, str, str | list[str]]] = []
    pending_list_label: str | None = None
    pending_list_items: list[str] = []

    def flush_pending_list() -> None:
        nonlocal pending_list_label, pending_list_items
        if pending_list_label is None:
            return
        if pending_list_items:
            sections.append((pending_list_label, "list", pending_list_items[:]))
        else:
            sections.append((pending_list_label, "scalar", ""))
        pending_list_label = None
        pending_list_items = []

    for raw_item in item_matches:
        item = collapse_html_whitespace(raw_item)
        if not item:
            continue

        label_only_match = AI_MESSAGE_LABEL_ONLY_RE.fullmatch(item)
        if label_only_match:
            flush_pending_list()
            pending_list_label = label_only_match.group(1).strip()
            pending_list_items = []
            continue

        label_with_content_match = AI_MESSAGE_LABEL_WITH_CONTENT_RE.fullmatch(item)
        if label_with_content_match:
            flush_pending_list()
            sections.append(
                (
                    label_with_content_match.group(1).strip(),
                    "scalar",
                    label_with_content_match.group(2).strip(),
                )
            )
            continue

        if pending_list_label is not None:
            pending_list_items.append(item)
        else:
            sections.append((None, "scalar", item))

    flush_pending_list()
    return render_ai_message_sections(sections)


def normalize_ai_authored_rich_text(value: str | None) -> str | None:
    raw = str(value or "").strip()
    if not raw or "AI MESSAGE DISCLAIMER" not in raw:
        return value

    body_match = re.search(r"<body\b[^>]*>(.*)</body>", raw, flags=re.IGNORECASE | re.DOTALL)
    inner = body_match.group(1) if body_match else raw
    inner = collapse_html_whitespace(inner)

    legacy_list_normalized = normalize_legacy_ai_message_list(inner)
    if legacy_list_normalized is not None:
        return legacy_list_normalized

    # Leave already-block-structured content alone unless it matches the legacy single-list shape above.
    if re.search(r"<(ul|ol|blockquote|pre)\b", raw, flags=re.IGNORECASE):
        return value

    disclaimer_match = AI_MESSAGE_HEADER_RE.match(inner)
    if not disclaimer_match:
        return value

    rest = disclaimer_match.group("rest").strip()
    sections: list[tuple[str | None, str, str | list[str]]] = []
    first_label = AI_MESSAGE_LABEL_RE.search(rest)
    intro = rest[: first_label.start()].strip() if first_label else rest
    if intro:
        sections.append((None, "scalar", intro))

    for match in AI_MESSAGE_LABEL_RE.finditer(rest[first_label.start() :] if first_label else ""):
        label_html = match.group(1).strip()
        content_html = match.group(2).strip()
        sections.append((label_html, "scalar", content_html))

    normalized = render_ai_message_sections(sections)
    if normalized is None:
        return value
    return normalized


def comment_payload_from_args(args: argparse.Namespace) -> dict[str, str]:
    text_value = load_inline_or_file_value(args.text, args.text_file, field_name="text")
    html_text_value = load_inline_or_file_value(
        args.html_text,
        args.html_text_file,
        field_name="html-text",
    )

    provided_count = sum(value is not None for value in (text_value, html_text_value))
    if provided_count != 1:
        raise SystemExit(
            "Pass exactly one of --text/--text-file or --html-text/--html-text-file"
        )

    if html_text_value is not None:
        return {"html_text": normalize_ai_authored_rich_text(html_text_value) or ""}
    return {"text": text_value or ""}


def maybe_wrap_data(payload: Any, no_wrap_data: bool) -> Any:
    if no_wrap_data:
        return payload
    if isinstance(payload, dict) and "data" in payload:
        return payload
    return {"data": payload}


def build_multipart(form_fields: dict[str, str], file_fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"----codex-asana-{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in form_fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8")
        )
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")

    for field, path_str in file_fields.items():
        path = Path(path_str).expanduser().resolve()
        content = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="{field}"; '
                f'filename="{path.name}"\r\n'
            ).encode("utf-8")
        )
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode("utf-8"))
        body.extend(content)
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def build_url(path_or_url: str, query: dict[str, str]) -> str:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        base = path_or_url
    else:
        path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
        base = f"{BASE_URL}{path}"
    if not query:
        return base
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{parse.urlencode(query, doseq=True)}"


def api_request(
    *,
    token: str,
    method: str,
    path_or_url: str,
    query: dict[str, str] | None = None,
    json_body: Any | None = None,
    multipart_form: dict[str, str] | None = None,
    multipart_files: dict[str, str] | None = None,
) -> Any:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    data = None

    if multipart_form or multipart_files:
        data, content_type = build_multipart(multipart_form or {}, multipart_files or {})
        headers["Content-Type"] = content_type
    elif json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(
        build_url(path_or_url, query or {}),
        data=data,
        headers=headers,
        method=method.upper(),
    )

    try:
        with request.urlopen(req) as response:
            payload = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {exc.reason}\n{detail}") from exc

    if not payload:
        return {}
    return json.loads(payload)


def maybe_paginate(token: str, first_response: Any, enabled: bool, limit_pages: int) -> Any:
    if not enabled:
        return first_response

    data = first_response.get("data")
    if not isinstance(data, list):
        return first_response

    merged = list(data)
    response = first_response
    pages = 1

    while response.get("next_page") and response["next_page"].get("uri"):
        if limit_pages and pages >= limit_pages:
            break
        response = api_request(
            token=token,
            method="GET",
            path_or_url=response["next_page"]["uri"],
        )
        page_data = response.get("data", [])
        if not isinstance(page_data, list):
            break
        merged.extend(page_data)
        pages += 1

    final_response = dict(first_response)
    final_response["data"] = merged
    final_response["pagination_pages"] = pages
    return final_response


def print_json(payload: Any, compact: bool) -> None:
    if compact:
        print(json.dumps(payload, separators=(",", ":")))
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def task_write_opt_fields() -> str:
    return (
        "gid,name,completed,completed_at,permalink_url,assignee.gid,assignee.name,"
        "due_on,due_at,parent.gid,parent.name"
    )


def story_write_opt_fields() -> str:
    return (
        "gid,created_at,resource_subtype,permalink_url,target.gid,target.name,"
        "target.permalink_url"
    )


def response_with_review_links(response: Any) -> Any:
    if not isinstance(response, dict):
        return response

    data = response.get("data")
    if not isinstance(data, dict):
        return response

    enriched = dict(response)
    review_url = str(data.get("permalink_url") or "").strip()
    if review_url:
        enriched["review_url"] = review_url

    target = data.get("target")
    if isinstance(target, dict):
        target_review_url = str(target.get("permalink_url") or "").strip()
        if target_review_url:
            enriched["target_review_url"] = target_review_url

    return enriched


def batch_actions_request(token: str, actions: list[dict[str, Any]]) -> Any:
    return api_request(
        token=token,
        method="POST",
        path_or_url="/batch",
        json_body={"data": {"actions": actions}},
    )


def batch_body_at(response: Any, index: int) -> Any:
    data = response.get("data", [])
    if index >= len(data):
        return {}
    item = data[index]
    if item.get("status_code", 200) >= 400:
        return {"error": item}
    return item.get("body", {})


def section_order_from_sections(sections: list[dict[str, Any]]) -> dict[str, int]:
    order_map: dict[str, int] = {}
    for index, section in enumerate(sections, start=1):
        section_gid = section.get("gid")
        if section_gid:
            order_map[section_gid] = index
    return order_map


def extract_image_urls_from_html(html: str | None) -> list[str]:
    if not html:
        return []
    return re.findall(r'<img[^>]+src="([^"]+)"', html)


def comment_stories_only(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        story
        for story in stories
        if story.get("type") == "comment" or story.get("resource_subtype") == "comment_added"
    ]


def recent_comment_stories(
    stories: list[dict[str, Any]],
    limit: int | None = None,
) -> list[dict[str, Any]]:
    comments = sorted(
        comment_stories_only(stories),
        key=lambda story: parse_iso_timestamp(story.get("created_at")),
    )
    if limit is None or limit <= 0:
        return comments
    return comments[-limit:]


def field_list(csv_fields: str) -> list[str]:
    return [field.strip() for field in csv_fields.split(",") if field.strip()]


def workspace_default(
    args: argparse.Namespace,
    context: dict[str, Any],
    cache: dict[str, Any] | None = None,
) -> str | None:
    value = getattr(args, "workspace", None) or context.get("workspace_gid")
    if not value:
        return None
    if value == context.get("workspace_name"):
        return context.get("workspace_gid")
    if cache:
        record = find_cached_record(cache, "workspaces", value, fields=("name",))
        if record:
            return str(record.get("gid"))
    return value


def team_default(
    args: argparse.Namespace,
    context: dict[str, Any],
    cache: dict[str, Any] | None = None,
) -> str | None:
    value = getattr(args, "team", None) or context.get("team_gid")
    if not value:
        return None
    teams = context.get("teams", {})
    if value in teams:
        return value
    lowered = value.casefold()
    for gid, name in teams.items():
        if str(name).casefold() == lowered:
            return gid
    if cache:
        record = find_cached_record(cache, "teams", value, fields=("name",))
        if record:
            return str(record.get("gid"))
    return value


def resolve_user_identifier(
    value: str | None,
    context: dict[str, Any],
    cache: dict[str, Any] | None = None,
) -> str | None:
    token = str(value or "").strip()
    if not token:
        return None
    if token == "me":
        return context.get("user_gid") or "me"
    if token == context.get("user_name") or token == context.get("user_gid"):
        return context.get("user_gid") or token
    if is_gid_like(token):
        return token
    if cache:
        record = find_cached_record(cache, "users", token, fields=("name", "email"))
        if record:
            return str(record.get("gid"))
    return token


def resolve_many_user_identifiers(
    values: list[str] | None,
    context: dict[str, Any],
    cache: dict[str, Any] | None = None,
) -> list[str]:
    resolved: list[str] = []
    for item in parse_many_gid(values):
        user_gid = resolve_user_identifier(item, context, cache)
        if user_gid:
            resolved.append(user_gid)
    return resolved


def add_common_output_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--compact", action="store_true", help="Print compact JSON")
    parser.add_argument("--token", help="Override PAT instead of using env/token file")


def task_opt_fields(default: str | None = None) -> str:
    return default or (
        "gid,name,completed,assignee.name,due_on,due_at,projects.name,"
        "memberships.section.name,parent.name,permalink_url"
    )


def project_assigned_task_opt_fields(default: str | None = None) -> str:
    return default or (
        "gid,name,completed,assignee.gid,assignee.name,due_on,due_at,permalink_url,"
        "parent.gid,parent.name,projects.gid,projects.name,memberships.project.gid,"
        "memberships.project.name,memberships.section.gid,memberships.section.name"
    )


def parent_task_context_opt_fields(default: str | None = None) -> str:
    return default or (
        "gid,name,permalink_url,memberships.project.gid,memberships.project.name,"
        "memberships.section.gid,memberships.section.name"
    )


def section_opt_fields(default: str | None = None) -> str:
    return default or "gid,name,project.name,created_at"


def tag_opt_fields(default: str | None = None) -> str:
    return default or "gid,name,color,notes,followers.name,permalink_url"


def story_opt_fields(default: str | None = None) -> str:
    return default or "gid,created_at,created_by.name,text,html_text,type,resource_subtype"


def story_detail_opt_fields(default: str | None = None) -> str:
    return default or (
        "gid,created_at,created_by.gid,created_by.name,text,html_text,type,"
        "resource_subtype,permalink_url,target.gid,target.name,target.resource_type,"
        "target.permalink_url"
    )


def custom_field_setting_opt_fields(default: str | None = None) -> str:
    return default or (
        "gid,is_important,custom_field.gid,custom_field.name,"
        "custom_field.resource_subtype,custom_field.display_value,"
        "custom_field.enum_options.name"
    )


def attachment_opt_fields(default: str | None = None) -> str:
    return default or "gid,name,resource_subtype,download_url,permanent_url,view_url,host,parent_type,parent.name"


def task_status_fields(default: str | None = None) -> str:
    return default or (
        "gid,name,completed,completed_at,permalink_url,assignee.name,due_on,due_at,"
        "memberships.project.gid,memberships.project.name,memberships.section.gid,"
        "memberships.section.name,custom_fields.gid,custom_fields.name,"
        "custom_fields.resource_subtype,custom_fields.display_value"
    )


def build_task_list_query(args: argparse.Namespace, default_fields: str | None = None) -> dict[str, str]:
    return {"opt_fields": args.opt_fields or task_opt_fields(default_fields)}


def post_task_relationship(
    args: argparse.Namespace,
    path: str,
    payload: dict[str, Any],
) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="POST",
        path_or_url=path,
        json_body={"data": payload},
    )
    print_json(response, args.compact)
    return response


def section_order_map(token: str, project_gid: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/projects/{project_gid}/sections",
        query={"opt_fields": section_opt_fields()},
    )
    sections = response.get("data", [])
    order_map: dict[str, int] = {}
    for index, section in enumerate(sections, start=1):
        section_gid = section.get("gid")
        if section_gid:
            order_map[section_gid] = index
    return sections, order_map


def section_task_positions_map(
    token: str,
    section_gids: list[str],
) -> dict[str, dict[str, int]]:
    unique_section_gids: list[str] = []
    seen: set[str] = set()
    for section_gid in section_gids:
        if section_gid and section_gid not in seen:
            seen.add(section_gid)
            unique_section_gids.append(section_gid)

    positions_by_section: dict[str, dict[str, int]] = {}
    for section_gid in unique_section_gids:
        section_tasks = api_request(
            token=token,
            method="GET",
            path_or_url=f"/sections/{section_gid}/tasks",
            query={"opt_fields": "gid"},
        ).get("data", [])
        positions_by_section[section_gid] = {
            str(section_task.get("gid")): index
            for index, section_task in enumerate(section_tasks, start=1)
            if isinstance(section_task, dict) and section_task.get("gid")
        }
    return positions_by_section


def command_request(args: argparse.Namespace) -> Any:
    token = get_token(args)
    query = parse_kv(args.query)
    if args.opt_fields:
        query["opt_fields"] = args.opt_fields
    if args.opt_expand:
        query["opt_expand"] = args.opt_expand

    json_body = None
    form_body = parse_kv(args.form)
    file_body = parse_kv(args.file)

    if args.data and args.data_file:
        raise SystemExit("Pass only one of --data or --data-file")

    if args.data:
        json_body = maybe_wrap_data(json.loads(args.data), args.no_wrap_data)
    elif args.data_file:
        json_body = maybe_wrap_data(json.loads(Path(args.data_file).read_text()), args.no_wrap_data)

    response = api_request(
        token=token,
        method=args.method,
        path_or_url=args.path,
        query=query,
        json_body=json_body,
        multipart_form=form_body,
        multipart_files=file_body,
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    print_json(response, args.compact)
    return response


def command_whoami(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url="/users/me",
        query={"opt_fields": "gid,name,email,workspaces.name"},
    )
    cache = load_cache()
    user = response.get("data", {})
    if isinstance(user, dict):
        cache_record(cache, "users", user_cache_record(user))
        workspaces = user.get("workspaces", [])
        if isinstance(workspaces, list):
            cache_records(cache, "workspaces", [workspace_cache_record(item) for item in workspaces if isinstance(item, dict)])
        cache["metadata"]["current_user_gid"] = user.get("gid")
        cache["metadata"]["current_user_name"] = user.get("name")
        save_cache(cache)
    print_json(response, args.compact)
    return response


def command_workspaces(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url="/users/me/workspaces",
    )
    cache = load_cache()
    workspaces = response.get("data", [])
    if isinstance(workspaces, list):
        cache_records(cache, "workspaces", [workspace_cache_record(item) for item in workspaces if isinstance(item, dict)])
        save_cache(cache)
    print_json(response, args.compact)
    return response


def command_teams(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    workspace = workspace_default(args, context, cache)
    if not workspace:
        raise SystemExit("No workspace GID provided and no default workspace in asana-context.json")
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/workspaces/{workspace}/teams",
    )
    teams = response.get("data", [])
    if isinstance(teams, list):
        cache_records(
            cache,
            "teams",
            [team_cache_record(item, workspace_gid=workspace) for item in teams if isinstance(item, dict)],
        )
        save_cache(cache)
    print_json(response, args.compact)
    return response


def command_projects(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    team = team_default(args, context, cache)
    if not team:
        raise SystemExit("No team GID provided and no default team in asana-context.json")
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/teams/{team}/projects",
    )
    projects = response.get("data", [])
    if isinstance(projects, list):
        cache_records(
            cache,
            "projects",
            [project_cache_record(item, team_gid=team) for item in projects if isinstance(item, dict)],
        )
        save_cache(cache)
    print_json(response, args.compact)
    return response


def command_users(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    workspace = workspace_default(args, context, cache)
    if not workspace:
        raise SystemExit("No workspace GID provided and no default workspace in asana-context.json")
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/workspaces/{workspace}/users",
        query={"opt_fields": args.opt_fields or "gid,name,email"},
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    users = response.get("data", [])
    if isinstance(users, list):
        cache_records(cache, "users", [user_cache_record(item) for item in users if isinstance(item, dict)])
        save_cache(cache)
    print_json(response, args.compact)
    return response


def command_task(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/tasks/{args.task_gid}",
        query={
            "opt_fields": args.opt_fields
            or "gid,name,resource_subtype,completed,assignee.name,due_on,due_at,"
            "projects.name,memberships.section.name,parent.name,permalink_url,notes",
        },
    )
    print_json(response, args.compact)
    return response


def command_story(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/stories/{args.story_gid}",
        query={"opt_fields": args.opt_fields or story_detail_opt_fields()},
    )
    response = response_with_review_links(response)
    print_json(response, args.compact)
    return response


def command_project(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/projects/{args.project_gid}",
        query={
            "opt_fields": args.opt_fields
            or "gid,name,team.name,owner.name,public,archived,current_status,"
            "default_view,created_at,permalink_url,notes",
        },
    )
    cache = load_cache()
    project = response.get("data", {})
    if isinstance(project, dict):
        cache_record(cache, "projects", project_cache_record(project))
        save_cache(cache)
    print_json(response, args.compact)
    return response


def command_project_tasks(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/projects/{args.project_gid}/tasks",
        query=build_task_list_query(args),
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    print_json(response, args.compact)
    return response


def command_sections(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/projects/{args.project_gid}/sections",
        query={"opt_fields": args.opt_fields or section_opt_fields()},
    )
    print_json(response, args.compact)
    return response


def command_section(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/sections/{args.section_gid}",
        query={"opt_fields": args.opt_fields or section_opt_fields("gid,name,project.name")},
    )
    print_json(response, args.compact)
    return response


def command_section_tasks(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/sections/{args.section_gid}/tasks",
        query=build_task_list_query(args),
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    print_json(response, args.compact)
    return response


def command_create_section(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="POST",
        path_or_url=f"/projects/{args.project_gid}/sections",
        json_body={"data": {"name": args.name}},
    )
    print_json(response, args.compact)
    return response


def command_update_section(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="PUT",
        path_or_url=f"/sections/{args.section_gid}",
        json_body={"data": {"name": args.name}},
    )
    print_json(response, args.compact)
    return response


def command_task_stories(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/tasks/{args.task_gid}/stories",
        query={"opt_fields": args.opt_fields or story_opt_fields()},
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    print_json(response, args.compact)
    return response


def command_task_comments(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/tasks/{args.task_gid}/stories",
        query={"opt_fields": args.opt_fields or story_opt_fields()},
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    comments = [
        story
        for story in response.get("data", [])
        if story.get("type") == "comment" or story.get("resource_subtype") == "comment_added"
    ]
    payload = {
        "data": comments,
        "comment_count": len(comments),
        "task_gid": args.task_gid,
    }
    print_json(payload, args.compact)
    return payload


def command_task_projects(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/tasks/{args.task_gid}/projects",
        query={"opt_fields": args.opt_fields or "gid,name"},
    )
    print_json(response, args.compact)
    return response


def command_task_status(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/tasks/{args.task_gid}",
        query={"opt_fields": args.opt_fields or task_status_fields()},
    )
    task = response.get("data", {})
    memberships = task.get("memberships") or []
    membership_summaries: list[dict[str, Any]] = []
    project_filter = args.project

    for membership in memberships:
        project = membership.get("project") or {}
        section = membership.get("section") or {}
        project_gid = project.get("gid")
        if project_filter and project_gid != project_filter:
            continue

        sections, order_map = section_order_map(token, project_gid) if project_gid else ([], {})
        section_gid = section.get("gid")
        section_name = section.get("name")
        section_position = order_map.get(section_gid)
        task_position = None

        if args.include_task_position and section_gid:
            section_tasks = api_request(
                token=token,
                method="GET",
                path_or_url=f"/sections/{section_gid}/tasks",
                query={"opt_fields": "gid"},
            ).get("data", [])
            for index, section_task in enumerate(section_tasks, start=1):
                if section_task.get("gid") == args.task_gid:
                    task_position = index
                    break

        membership_summaries.append(
            {
                "project_gid": project_gid,
                "project_name": project.get("name"),
                "section_gid": section_gid,
                "section_name": section_name,
                "section_position": section_position,
                "section_count": len(sections),
                "task_position_in_section": task_position,
            }
        )

    payload = {
        "task_gid": task.get("gid"),
        "name": task.get("name"),
        "completed": task.get("completed"),
        "completed_at": task.get("completed_at"),
        "permalink_url": task.get("permalink_url"),
        "assignee": task.get("assignee"),
        "due_on": task.get("due_on"),
        "due_at": task.get("due_at"),
        "custom_fields": task.get("custom_fields", []),
        "memberships": membership_summaries,
    }
    print_json(payload, args.compact)
    return payload


def command_project_board(args: argparse.Namespace) -> Any:
    token = get_token(args)
    sections, order_map = section_order_map(token, args.project_gid)
    section_payloads: list[dict[str, Any]] = []

    for section in sections:
        section_gid = section.get("gid")
        tasks_response = api_request(
            token=token,
            method="GET",
            path_or_url=f"/sections/{section_gid}/tasks",
            query={
                "opt_fields": args.opt_fields
                or "gid,name,completed,completed_at,assignee.name,due_on,due_at,"
                "custom_fields.name,custom_fields.display_value"
            },
        )
        tasks = []
        for index, task in enumerate(tasks_response.get("data", []), start=1):
            task_copy = dict(task)
            task_copy["task_position_in_section"] = index
            tasks.append(task_copy)

        section_name = section.get("name")
        section_payloads.append(
            {
                "gid": section_gid,
                "name": section_name,
                "section_position": order_map.get(section_gid),
                "task_count": len(tasks),
                "tasks": tasks,
            }
        )

    payload = {
        "project_gid": args.project_gid,
        "sections": section_payloads,
    }
    print_json(payload, args.compact)
    return payload


def command_task_bundle(args: argparse.Namespace) -> Any:
    token = get_token(args)
    actions = [
        {
            "method": "get",
            "relative_path": f"/tasks/{args.task_gid}",
            "options": {
                "fields": field_list(
                    args.task_opt_fields
                    or "gid,name,notes,html_notes,resource_subtype,completed,completed_at,assignee.gid,assignee.name,"
                    "due_on,due_at,permalink_url,parent.gid,parent.name,memberships.project.gid,memberships.project.name,"
                    "memberships.section.gid,memberships.section.name,custom_fields.gid,custom_fields.name,"
                    "custom_fields.resource_subtype,custom_fields.display_value,custom_fields.enum_value.name"
                )
            },
        },
        {
            "method": "get",
            "relative_path": f"/tasks/{args.task_gid}/stories",
            "options": {"fields": field_list(args.story_opt_fields or story_opt_fields())},
        },
        {
            "method": "get",
            "relative_path": f"/tasks/{args.task_gid}/attachments",
            "options": {
                "fields": field_list(
                    args.attachment_opt_fields
                    or "gid,name,resource_subtype,download_url,permanent_url,view_url,host,parent_type,parent.name"
                )
            },
        },
    ]
    if args.project_gid:
        actions.append(
            {
                "method": "get",
                "relative_path": f"/projects/{args.project_gid}/sections",
                "options": {"fields": field_list(section_opt_fields())},
            }
        )
        actions.append(
            {
                "method": "get",
                "relative_path": f"/projects/{args.project_gid}/custom_field_settings",
                "options": {"fields": field_list(custom_field_setting_opt_fields())},
            }
        )

    batch_response = batch_actions_request(token, actions)
    task = batch_body_at(batch_response, 0).get("data", {})
    stories = batch_body_at(batch_response, 1).get("data", [])
    attachments = batch_body_at(batch_response, 2).get("data", [])
    sections = batch_body_at(batch_response, 3).get("data", []) if args.project_gid else []
    project_custom_field_settings = batch_body_at(batch_response, 4).get("data", []) if args.project_gid else []
    section_order = section_order_from_sections(sections)
    comments = comment_stories_only(stories)

    memberships = []
    for membership in task.get("memberships", []):
        project = membership.get("project") or {}
        if args.project_gid and project.get("gid") != args.project_gid:
            continue
        section = membership.get("section") or {}
        section_gid = section.get("gid")
        memberships.append(
            {
                "project_gid": project.get("gid"),
                "project_name": project.get("name"),
                "section_gid": section_gid,
                "section_name": section.get("name"),
                "section_position": section_order.get(section_gid),
            }
        )

    image_urls = []
    for attachment in attachments:
        for key in ("download_url", "view_url", "permanent_url"):
            value = attachment.get(key)
            if isinstance(value, str) and value not in image_urls:
                image_urls.append(value)
    for comment in comments:
        for url in extract_image_urls_from_html(comment.get("html_text")):
            if url not in image_urls:
                image_urls.append(url)
    if task.get("html_notes"):
        for url in extract_image_urls_from_html(task.get("html_notes")):
            if url not in image_urls:
                image_urls.append(url)

    payload = {
        "task": task,
        "workflow_context": {
            "project_gid": args.project_gid,
            "memberships": memberships,
            "section_order": [
                {"gid": section.get("gid"), "name": section.get("name"), "section_position": section_order.get(section.get("gid"))}
                for section in sections
            ],
        },
        "comments": {
            "data": comments,
            "comment_count": len(comments),
        },
        "attachments": attachments,
        "project_custom_field_settings": project_custom_field_settings,
        "image_urls": image_urls,
        "asana_permalink": task.get("permalink_url"),
    }
    print_json(payload, args.compact)
    return payload


def command_add_task_project(args: argparse.Namespace) -> Any:
    payload: dict[str, Any] = {"project": args.project_gid}
    if args.section:
        payload["section"] = args.section
    if args.insert_before is not None:
        payload["insert_before"] = nullable_arg(args.insert_before)
    if args.insert_after is not None:
        payload["insert_after"] = nullable_arg(args.insert_after)
    return post_task_relationship(args, f"/tasks/{args.task_gid}/addProject", payload)


def command_remove_task_project(args: argparse.Namespace) -> Any:
    return post_task_relationship(
        args,
        f"/tasks/{args.task_gid}/removeProject",
        {"project": args.project_gid},
    )


def command_add_task_followers(args: argparse.Namespace) -> Any:
    context = load_context()
    cache = load_cache()
    return post_task_relationship(
        args,
        f"/tasks/{args.task_gid}/addFollowers",
        {"followers": resolve_many_user_identifiers(args.followers, context, cache)},
    )


def command_remove_task_followers(args: argparse.Namespace) -> Any:
    context = load_context()
    cache = load_cache()
    return post_task_relationship(
        args,
        f"/tasks/{args.task_gid}/removeFollowers",
        {"followers": resolve_many_user_identifiers(args.followers, context, cache)},
    )


def command_task_tags(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/tasks/{args.task_gid}/tags",
        query={"opt_fields": args.opt_fields or tag_opt_fields("gid,name,color")},
    )
    print_json(response, args.compact)
    return response


def command_tags(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    workspace = workspace_default(args, context, cache)
    if not workspace:
        raise SystemExit("No workspace GID provided and no default workspace in asana-context.json")
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/workspaces/{workspace}/tags",
        query={"opt_fields": args.opt_fields or tag_opt_fields("gid,name,color")},
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    tags = response.get("data", [])
    if isinstance(tags, list):
        cache_records(cache, "tags", [tag_cache_record(item) for item in tags if isinstance(item, dict)])
        save_cache(cache)
    print_json(response, args.compact)
    return response


def command_workspace_custom_fields(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    workspace = workspace_default(args, context, cache)
    if not workspace:
        raise SystemExit("No workspace GID provided and no default workspace in asana-context.json")
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/workspaces/{workspace}/custom_fields",
        query={"opt_fields": args.opt_fields or "gid,name,resource_subtype,enum_options.name,enabled"},
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    print_json(response, args.compact)
    return response


def command_team_custom_fields(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    team = team_default(args, context, cache)
    if not team:
        raise SystemExit("No team GID provided and no default team in asana-context.json")
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/teams/{team}/custom_field_settings",
        query={"opt_fields": args.opt_fields or custom_field_setting_opt_fields()},
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    print_json(response, args.compact)
    return response


def command_project_custom_fields(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/projects/{args.project_gid}/custom_field_settings",
        query={"opt_fields": args.opt_fields or custom_field_setting_opt_fields()},
    )
    print_json(response, args.compact)
    return response


def command_task_custom_fields(args: argparse.Namespace) -> Any:
    token = get_token(args)
    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/tasks/{args.task_gid}",
        query={
            "opt_fields": args.opt_fields
            or "gid,name,custom_fields.gid,custom_fields.name,custom_fields.resource_subtype,"
            "custom_fields.display_value,custom_fields.enum_value.name"
        },
    )
    task = response.get("data", {})
    payload = {
        "task_gid": task.get("gid"),
        "name": task.get("name"),
        "custom_fields": task.get("custom_fields", []),
    }
    print_json(payload, args.compact)
    return payload


def command_create_custom_field(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    workspace = workspace_default(args, context, cache)
    if not workspace:
        raise SystemExit("No workspace GID provided and no default workspace in asana-context.json")
    payload: dict[str, Any] = {
        "workspace": workspace,
        "name": args.name,
        "resource_subtype": args.resource_subtype,
    }
    if args.description:
        payload["description"] = args.description
    if args.precision is not None:
        payload["precision"] = args.precision
    if args.enum_option:
        payload["enum_options"] = [{"name": name} for name in args.enum_option]
    response = api_request(
        token=token,
        method="POST",
        path_or_url="/custom_fields",
        json_body={"data": payload},
    )
    print_json(response, args.compact)
    return response


def command_batch(args: argparse.Namespace) -> Any:
    token = get_token(args)
    if bool(args.actions) == bool(args.actions_file):
        raise SystemExit("Pass exactly one of --actions or --actions-file")
    actions_payload = args.actions
    if args.actions_file:
        actions_payload = Path(args.actions_file).read_text()
    actions = json.loads(actions_payload)
    if not isinstance(actions, list):
        raise SystemExit("Batch actions must be a JSON array")
    response = api_request(
        token=token,
        method="POST",
        path_or_url="/batch",
        json_body={"data": {"actions": actions}},
    )
    print_json(response, args.compact)
    return response


def command_create_tag(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    workspace = workspace_default(args, context, cache)
    if not workspace:
        raise SystemExit("No workspace GID provided and no default workspace in asana-context.json")
    payload: dict[str, Any] = {"workspace": workspace, "name": args.name}
    if args.color:
        payload["color"] = args.color
    if args.notes:
        payload["notes"] = args.notes
    response = api_request(
        token=token,
        method="POST",
        path_or_url="/tags",
        json_body={"data": payload},
    )
    print_json(response, args.compact)
    return response


def command_add_task_tag(args: argparse.Namespace) -> Any:
    return post_task_relationship(
        args,
        f"/tasks/{args.task_gid}/addTag",
        {"tag": args.tag_gid},
    )


def command_remove_task_tag(args: argparse.Namespace) -> Any:
    return post_task_relationship(
        args,
        f"/tasks/{args.task_gid}/removeTag",
        {"tag": args.tag_gid},
    )


def command_add_task_dependencies(args: argparse.Namespace) -> Any:
    return post_task_relationship(
        args,
        f"/tasks/{args.task_gid}/addDependencies",
        {"dependencies": parse_many_gid(args.dependencies)},
    )


def command_remove_task_dependencies(args: argparse.Namespace) -> Any:
    return post_task_relationship(
        args,
        f"/tasks/{args.task_gid}/removeDependencies",
        {"dependencies": parse_many_gid(args.dependencies)},
    )


def command_search_tasks(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    workspace = workspace_default(args, context, cache)
    if not workspace:
        raise SystemExit("No workspace GID provided and no default workspace in asana-context.json")

    query: dict[str, str] = {
        "text": args.text,
        "opt_fields": args.opt_fields
        or "gid,name,completed,assignee.name,due_on,projects.name,permalink_url",
    }
    optional_values = {
        "projects.any": args.project,
        "assignee.any": resolve_user_identifier(args.assignee, context, cache),
        "completed": str(args.completed).lower() if args.completed is not None else None,
    }
    for key, value in optional_values.items():
        if value is not None:
            query[key] = value

    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/workspaces/{workspace}/tasks/search",
        query=query,
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)
    tasks = response.get("data", [])
    if isinstance(tasks, list):
        assignees = [
            user_cache_record(task["assignee"])
            for task in tasks
            if isinstance(task, dict) and isinstance(task.get("assignee"), dict)
        ]
        if assignees:
            cache_records(cache, "users", assignees)
            save_cache(cache)
    print_json(response, args.compact)
    return response


def fetch_parent_task_context_map(token: str, parent_gids: list[str]) -> dict[str, dict[str, Any]]:
    unique_parent_gids: list[str] = []
    seen: set[str] = set()
    for parent_gid in parent_gids:
        if parent_gid and parent_gid not in seen:
            seen.add(parent_gid)
            unique_parent_gids.append(parent_gid)

    parent_context_map: dict[str, dict[str, Any]] = {}
    for start in range(0, len(unique_parent_gids), 10):
        chunk = unique_parent_gids[start : start + 10]
        actions = [
            {
                "method": "get",
                "relative_path": f"/tasks/{parent_gid}",
                "options": {"fields": field_list(parent_task_context_opt_fields())},
            }
            for parent_gid in chunk
        ]
        batch_response = batch_actions_request(token, actions)
        for index, parent_gid in enumerate(chunk):
            parent = batch_body_at(batch_response, index).get("data", {})
            if parent:
                parent_context_map[parent_gid] = parent
    return parent_context_map


def fetch_task_activity_context_map(
    token: str,
    task_gids: list[str],
    *,
    include_comments: bool,
    comment_limit: int,
    include_attachments: bool,
) -> dict[str, dict[str, Any]]:
    activity_map: dict[str, dict[str, Any]] = {
        task_gid: {}
        for task_gid in task_gids
        if task_gid
    }
    if not include_comments and not include_attachments:
        return activity_map

    actions: list[tuple[str, str, dict[str, Any]]] = []
    for task_gid in task_gids:
        if not task_gid:
            continue
        if include_comments:
            actions.append(
                (
                    task_gid,
                    "comments",
                    {
                        "method": "get",
                        "relative_path": f"/tasks/{task_gid}/stories",
                        "options": {"fields": field_list(story_opt_fields())},
                    },
                )
            )
        if include_attachments:
            actions.append(
                (
                    task_gid,
                    "attachments",
                    {
                        "method": "get",
                        "relative_path": f"/tasks/{task_gid}/attachments",
                        "options": {"fields": field_list(attachment_opt_fields())},
                    },
                )
            )

    max_batch_actions = 10
    for start in range(0, len(actions), max_batch_actions):
        chunk = actions[start : start + max_batch_actions]
        batch_response = batch_actions_request(
            token,
            [action for _, _, action in chunk],
        )
        for index, (task_gid, kind, _) in enumerate(chunk):
            body = batch_body_at(batch_response, index).get("data", [])
            if not isinstance(body, list):
                continue
            task_activity = activity_map.setdefault(task_gid, {})
            if kind == "comments":
                comments = recent_comment_stories(body, comment_limit)
                task_activity["recent_comments"] = comments
                task_activity["comment_count"] = len(comment_stories_only(body))
                existing_image_urls = task_activity.setdefault("image_urls", [])
                for comment in comments:
                    for url in extract_image_urls_from_html(comment.get("html_text")):
                        if url not in existing_image_urls:
                            existing_image_urls.append(url)
            elif kind == "attachments":
                task_activity["attachments"] = body
                task_activity["attachment_count"] = len(body)
                existing_image_urls = task_activity.setdefault("image_urls", [])
                for attachment in body:
                    for key in ("download_url", "view_url", "permanent_url"):
                        value = attachment.get(key) if isinstance(attachment, dict) else None
                        if isinstance(value, str) and value not in existing_image_urls:
                            existing_image_urls.append(value)

    return activity_map


def command_project_assigned_tasks(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    workspace = workspace_default(args, context, cache)
    if not workspace:
        raise SystemExit("No workspace GID provided and no default workspace in asana-context.json")

    assignee = resolve_user_identifier(args.assignee or context.get("user_gid") or "me", context, cache)

    query: dict[str, str] = {
        "projects.any": args.project_gid,
        "assignee.any": assignee,
        "opt_fields": args.opt_fields or project_assigned_task_opt_fields(),
    }
    if args.completed is not None:
        query["completed"] = str(args.completed).lower()

    response = api_request(
        token=token,
        method="GET",
        path_or_url=f"/workspaces/{workspace}/tasks/search",
        query=query,
    )
    response = maybe_paginate(token, response, args.paginate, args.limit_pages)

    tasks = response.get("data", [])
    if not isinstance(tasks, list):
        print_json(response, args.compact)
        return response

    parent_context_map = fetch_parent_task_context_map(
        token,
        [
            str(task.get("parent", {}).get("gid"))
            for task in tasks
            if isinstance(task, dict) and isinstance(task.get("parent"), dict) and task["parent"].get("gid")
        ],
    )
    sections, section_order = section_order_map(token, args.project_gid)
    activity_context_map = fetch_task_activity_context_map(
        token,
        [
            str(task.get("gid"))
            for task in tasks
            if isinstance(task, dict) and task.get("gid")
        ],
        include_comments=args.include_comments,
        comment_limit=args.comment_limit,
        include_attachments=args.include_attachments,
    )

    section_positions: dict[str, dict[str, int]] = {}
    if args.include_task_position:
        relevant_section_gids: list[str] = []
        for task in tasks:
            if not isinstance(task, dict):
                continue
            parent = task.get("parent")
            parent_gid = parent.get("gid") if isinstance(parent, dict) else None
            parent_context = parent_context_map.get(str(parent_gid)) if parent_gid else None
            memberships = task.get("memberships")
            effective_memberships = memberships if memberships else parent_context.get("memberships", []) if parent_context else []
            for membership in effective_memberships:
                if not isinstance(membership, dict):
                    continue
                section = membership.get("section") or {}
                section_gid = section.get("gid")
                if section_gid:
                    relevant_section_gids.append(str(section_gid))
        section_positions = section_task_positions_map(token, relevant_section_gids)

    enriched_tasks: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            enriched_tasks.append(task)
            continue

        task_payload = dict(task)
        parent = task_payload.get("parent")
        parent_gid = parent.get("gid") if isinstance(parent, dict) else None
        parent_context = parent_context_map.get(str(parent_gid)) if parent_gid else None
        memberships = task_payload.get("memberships")
        effective_memberships = memberships if memberships else parent_context.get("memberships", []) if parent_context else []
        effective_membership_summaries: list[dict[str, Any]] = []
        task_gid = str(task_payload.get("gid") or "")
        for membership in effective_memberships:
            if not isinstance(membership, dict):
                continue
            project = membership.get("project") or {}
            section = membership.get("section") or {}
            section_gid = str(section.get("gid") or "")
            effective_membership_summaries.append(
                {
                    "project_gid": project.get("gid"),
                    "project_name": project.get("name"),
                    "section_gid": section.get("gid"),
                    "section_name": section.get("name"),
                    "section_position": section_order.get(section_gid) if section_gid else None,
                    "task_position_in_section": section_positions.get(section_gid, {}).get(task_gid)
                    if section_gid
                    else None,
                }
            )

        task_payload["is_subtask"] = bool(parent_gid)
        task_payload["effective_memberships"] = effective_memberships
        task_payload["effective_membership_summaries"] = effective_membership_summaries
        if parent_context:
            task_payload["parent_context"] = parent_context
        activity_context = activity_context_map.get(task_gid)
        if activity_context:
            task_payload.update(activity_context)

        enriched_tasks.append(task_payload)

    payload = dict(response)
    payload["data"] = enriched_tasks
    payload["project_gid"] = args.project_gid
    payload["workspace_gid"] = workspace
    payload["assignee"] = assignee
    payload["includes_subtasks"] = True
    payload["workflow_context"] = {
        "section_order": [
            {
                "gid": section.get("gid"),
                "name": section.get("name"),
                "section_position": section_order.get(section.get("gid")),
            }
            for section in sections
        ],
    }
    payload["context_includes"] = {
        "section_order": True,
        "task_position_in_section": bool(args.include_task_position),
        "recent_comments": bool(args.include_comments),
        "attachments": bool(args.include_attachments),
    }
    payload["subtask_count"] = sum(1 for task in enriched_tasks if isinstance(task, dict) and task.get("is_subtask"))
    assignees = [
        user_cache_record(task["assignee"])
        for task in enriched_tasks
        if isinstance(task, dict) and isinstance(task.get("assignee"), dict)
    ]
    if assignees:
        cache_records(cache, "users", assignees)
        save_cache(cache)
    print_json(payload, args.compact)
    return payload


def build_task_payload(
    args: argparse.Namespace,
    context: dict[str, Any],
    cache: dict[str, Any],
    is_create: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for attr in ("name", "notes", "due_on", "due_at"):
        value = getattr(args, attr, None)
        if value:
            payload[attr] = value

    html_notes = getattr(args, "html_notes", None)
    if html_notes:
        payload["html_notes"] = normalize_ai_authored_rich_text(html_notes) or ""

    assignee = resolve_user_identifier(getattr(args, "assignee", None), context, cache)
    if assignee:
        payload["assignee"] = assignee

    if getattr(args, "completed", None) is not None:
        payload["completed"] = args.completed

    project = getattr(args, "project", None)
    workspace = workspace_default(args, context, cache)
    parent = getattr(args, "parent", None)

    if project:
        payload["projects"] = [project]
    elif is_create and workspace:
        payload["workspace"] = workspace

    if parent:
        payload["parent"] = parent

    if args.custom_field:
        payload["custom_fields"] = parse_custom_fields(args.custom_field)

    return payload


def parse_custom_fields(items: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Expected custom field assignment <gid>=<value>, got: {item}")
        gid, value = item.split("=", 1)
        parsed[gid] = value
    return parsed


def command_create_task(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    payload = build_task_payload(args, context, cache, is_create=True)
    response = api_request(
        token=token,
        method="POST",
        path_or_url="/tasks",
        query={"opt_fields": task_write_opt_fields()},
        json_body={"data": payload},
    )
    task = response.get("data", {})
    if isinstance(task, dict) and isinstance(task.get("assignee"), dict):
        cache_record(cache, "users", user_cache_record(task["assignee"]))
        save_cache(cache)
    enriched = response_with_review_links(response)
    print_json(enriched, args.compact)
    return enriched


def command_update_task(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    payload = build_task_payload(args, context, cache, is_create=False)
    response = api_request(
        token=token,
        method="PUT",
        path_or_url=f"/tasks/{args.task_gid}",
        query={"opt_fields": task_write_opt_fields()},
        json_body={"data": payload},
    )
    task = response.get("data", {})
    if isinstance(task, dict) and isinstance(task.get("assignee"), dict):
        cache_record(cache, "users", user_cache_record(task["assignee"]))
        save_cache(cache)
    enriched = response_with_review_links(response)
    print_json(enriched, args.compact)
    return enriched


def command_comment_task(args: argparse.Namespace) -> Any:
    token = get_token(args)
    payload = comment_payload_from_args(args)
    response = api_request(
        token=token,
        method="POST",
        path_or_url=f"/tasks/{args.task_gid}/stories",
        query={"opt_fields": story_write_opt_fields()},
        json_body={"data": payload},
    )
    enriched = response_with_review_links(response)
    print_json(enriched, args.compact)
    return enriched


def command_update_story(args: argparse.Namespace) -> Any:
    token = get_token(args)
    payload = comment_payload_from_args(args)
    response = api_request(
        token=token,
        method="PUT",
        path_or_url=f"/stories/{args.story_gid}",
        query={"opt_fields": story_write_opt_fields()},
        json_body={"data": payload},
    )
    enriched = response_with_review_links(response)
    print_json(enriched, args.compact)
    return enriched


def command_create_project(args: argparse.Namespace) -> Any:
    token = get_token(args)
    context = load_context()
    cache = load_cache()
    team = team_default(args, context, cache)
    payload = {"name": args.name}
    if team:
        payload["team"] = team
    elif workspace_default(args, context, cache):
        payload["workspace"] = workspace_default(args, context, cache)
    if args.notes:
        payload["notes"] = args.notes

    response = api_request(
        token=token,
        method="POST",
        path_or_url="/projects",
        json_body={"data": payload},
    )
    project = response.get("data", {})
    if isinstance(project, dict):
        cache_record(cache, "projects", project_cache_record(project, team_gid=team))
        save_cache(cache)
    print_json(response, args.compact)
    return response


def command_update_project(args: argparse.Namespace) -> Any:
    token = get_token(args)
    cache = load_cache()
    payload = {"name": args.name} if args.name else {}
    if args.notes:
        payload["notes"] = args.notes
    if args.archived is not None:
        payload["archived"] = args.archived
    response = api_request(
        token=token,
        method="PUT",
        path_or_url=f"/projects/{args.project_gid}",
        json_body={"data": payload},
    )
    project = response.get("data", {})
    if isinstance(project, dict):
        cache_record(cache, "projects", project_cache_record(project))
        save_cache(cache)
    print_json(response, args.compact)
    return response


def command_show_context(args: argparse.Namespace) -> Any:
    response = load_context()
    print_json(response, args.compact)
    return response


def command_show_cache(args: argparse.Namespace) -> Any:
    response = load_cache()
    print_json(response, args.compact)
    return response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Asana API helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    request_parser = subparsers.add_parser("request", help="Run a generic Asana API request")
    request_parser.add_argument("method", help="HTTP method, e.g. GET/POST/PUT/DELETE")
    request_parser.add_argument("path", help="Relative /path or full URL")
    request_parser.add_argument("--query", action="append", help="Query param as key=value")
    request_parser.add_argument("--opt-fields", help="Asana opt_fields value")
    request_parser.add_argument("--opt-expand", help="Asana opt_expand value")
    request_parser.add_argument("--data", help="JSON payload string")
    request_parser.add_argument("--data-file", help="Path to JSON payload file")
    request_parser.add_argument(
        "--no-wrap-data",
        action="store_true",
        help="Do not auto-wrap JSON payloads in {\"data\": ...}",
    )
    request_parser.add_argument("--form", action="append", help="Multipart form field as key=value")
    request_parser.add_argument("--file", action="append", help="Multipart file field as field=/abs/path")
    request_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    request_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(request_parser)
    request_parser.set_defaults(func=command_request)

    whoami_parser = subparsers.add_parser("whoami", help="Show the authenticated user")
    add_common_output_flags(whoami_parser)
    whoami_parser.set_defaults(func=command_whoami)

    workspaces_parser = subparsers.add_parser("workspaces", help="List workspaces for the authenticated user")
    add_common_output_flags(workspaces_parser)
    workspaces_parser.set_defaults(func=command_workspaces)

    teams_parser = subparsers.add_parser("teams", help="List teams in a workspace")
    teams_parser.add_argument("--workspace", help="Workspace GID override")
    add_common_output_flags(teams_parser)
    teams_parser.set_defaults(func=command_teams)

    users_parser = subparsers.add_parser("users", help="List users in a workspace")
    users_parser.add_argument("--workspace", help="Workspace GID override")
    users_parser.add_argument("--opt-fields", help="Override result fields")
    users_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    users_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(users_parser)
    users_parser.set_defaults(func=command_users)

    projects_parser = subparsers.add_parser("projects", help="List projects for a team")
    projects_parser.add_argument("--team", help="Team GID or exact team name from asana-context.json")
    add_common_output_flags(projects_parser)
    projects_parser.set_defaults(func=command_projects)

    task_parser = subparsers.add_parser("task", help="Inspect a task")
    task_parser.add_argument("task_gid")
    task_parser.add_argument("--opt-fields", help="Override task fields")
    add_common_output_flags(task_parser)
    task_parser.set_defaults(func=command_task)

    story_parser = subparsers.add_parser("story", help="Inspect a story/comment by gid")
    story_parser.add_argument("story_gid")
    story_parser.add_argument("--opt-fields", help="Override story fields")
    add_common_output_flags(story_parser)
    story_parser.set_defaults(func=command_story)

    task_bundle_parser = subparsers.add_parser(
        "task-bundle",
        help="Fetch task, comments, attachments, and project workflow context in a single batch call",
    )
    task_bundle_parser.add_argument("task_gid")
    task_bundle_parser.add_argument(
        "--project-gid",
        help="Project GID to include section order and project custom field settings",
    )
    task_bundle_parser.add_argument("--task-opt-fields", help="Override task fields")
    task_bundle_parser.add_argument("--story-opt-fields", help="Override story fields")
    task_bundle_parser.add_argument("--attachment-opt-fields", help="Override attachment fields")
    add_common_output_flags(task_bundle_parser)
    task_bundle_parser.set_defaults(func=command_task_bundle)

    task_status_parser = subparsers.add_parser("task-status", help="Summarize completion and board-column status for a task")
    task_status_parser.add_argument("task_gid")
    task_status_parser.add_argument("--project", help="Limit membership analysis to one project GID")
    task_status_parser.add_argument("--opt-fields", help="Override task fields")
    task_status_parser.add_argument(
        "--include-task-position",
        action="store_true",
        help="Also look up the task's position inside its current section",
    )
    add_common_output_flags(task_status_parser)
    task_status_parser.set_defaults(func=command_task_status)

    project_parser = subparsers.add_parser("project", help="Inspect a project")
    project_parser.add_argument("project_gid")
    project_parser.add_argument("--opt-fields", help="Override project fields")
    add_common_output_flags(project_parser)
    project_parser.set_defaults(func=command_project)

    board_parser = subparsers.add_parser("board", help="Return project sections in order with tasks in each section")
    board_parser.add_argument("project_gid")
    board_parser.add_argument("--opt-fields", help="Override per-task fields in board output")
    add_common_output_flags(board_parser)
    board_parser.set_defaults(func=command_project_board)

    project_tasks_parser = subparsers.add_parser("project-tasks", help="List tasks in a project")
    project_tasks_parser.add_argument("project_gid")
    project_tasks_parser.add_argument("--opt-fields", help="Override task fields")
    project_tasks_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    project_tasks_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(project_tasks_parser)
    project_tasks_parser.set_defaults(func=command_project_tasks)

    project_assigned_parser = subparsers.add_parser(
        "project-assigned-tasks",
        help="List assigned work in a project, including matching subtasks with parent section context",
    )
    project_assigned_parser.add_argument("project_gid")
    project_assigned_parser.add_argument("--workspace", help="Workspace GID override")
    project_assigned_parser.add_argument(
        "--assignee",
        help="Assignee filter, defaults to the current user from asana-context.json; accepts gid, exact cached name, or exact cached email",
    )
    project_assigned_parser.add_argument("--completed", type=parse_bool, help="Filter by completion")
    project_assigned_parser.add_argument("--opt-fields", help="Override result fields")
    project_assigned_parser.add_argument(
        "--include-task-position",
        action="store_true",
        help="Also look up each task's position inside its effective board section",
    )
    project_assigned_parser.add_argument(
        "--include-comments",
        action="store_true",
        help="Include recent comment context for each task",
    )
    project_assigned_parser.add_argument(
        "--comment-limit",
        type=int,
        default=3,
        help="Maximum number of recent comments to keep per task when --include-comments is set",
    )
    project_assigned_parser.add_argument(
        "--include-attachments",
        action="store_true",
        help="Include task attachments and derived image URLs for each task",
    )
    project_assigned_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    project_assigned_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(project_assigned_parser)
    project_assigned_parser.set_defaults(func=command_project_assigned_tasks)

    sections_parser = subparsers.add_parser("sections", help="List sections in a project")
    sections_parser.add_argument("project_gid")
    sections_parser.add_argument("--opt-fields", help="Override section fields")
    add_common_output_flags(sections_parser)
    sections_parser.set_defaults(func=command_sections)

    section_parser = subparsers.add_parser("section", help="Inspect a section")
    section_parser.add_argument("section_gid")
    section_parser.add_argument("--opt-fields", help="Override section fields")
    add_common_output_flags(section_parser)
    section_parser.set_defaults(func=command_section)

    section_tasks_parser = subparsers.add_parser("section-tasks", help="List tasks in a section")
    section_tasks_parser.add_argument("section_gid")
    section_tasks_parser.add_argument("--opt-fields", help="Override task fields")
    section_tasks_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    section_tasks_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(section_tasks_parser)
    section_tasks_parser.set_defaults(func=command_section_tasks)

    create_section_parser = subparsers.add_parser("create-section", help="Create a section in a project")
    create_section_parser.add_argument("project_gid")
    create_section_parser.add_argument("--name", required=True)
    add_common_output_flags(create_section_parser)
    create_section_parser.set_defaults(func=command_create_section)

    update_section_parser = subparsers.add_parser("update-section", help="Rename a section")
    update_section_parser.add_argument("section_gid")
    update_section_parser.add_argument("--name", required=True)
    add_common_output_flags(update_section_parser)
    update_section_parser.set_defaults(func=command_update_section)

    search_parser = subparsers.add_parser("search-tasks", help="Search tasks within a workspace")
    search_parser.add_argument("--text", required=True, help="Search text")
    search_parser.add_argument("--workspace", help="Workspace GID override")
    search_parser.add_argument("--project", help="Project GID filter")
    search_parser.add_argument("--assignee", help="Assignee filter, e.g. me, user gid, exact cached user name, or exact cached email")
    search_parser.add_argument("--completed", type=parse_bool, help="Filter by completion")
    search_parser.add_argument("--opt-fields", help="Override result fields")
    search_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    search_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(search_parser)
    search_parser.set_defaults(func=command_search_tasks)

    create_task_parser = subparsers.add_parser("create-task", help="Create a task")
    create_task_parser.add_argument("--name", required=True)
    create_task_parser.add_argument("--workspace", help="Workspace GID override")
    create_task_parser.add_argument("--project", help="Project GID")
    create_task_parser.add_argument("--parent", help="Parent task GID")
    create_task_parser.add_argument("--assignee", help="Assignee gid, me, exact cached user name, or exact cached email")
    create_task_parser.add_argument("--notes")
    create_task_parser.add_argument("--html-notes")
    create_task_parser.add_argument("--due-on")
    create_task_parser.add_argument("--due-at")
    create_task_parser.add_argument("--custom-field", action="append", default=[], help="Custom field as gid=value")
    add_common_output_flags(create_task_parser)
    create_task_parser.set_defaults(func=command_create_task)

    update_task_parser = subparsers.add_parser("update-task", help="Update a task")
    update_task_parser.add_argument("task_gid")
    update_task_parser.add_argument("--name")
    update_task_parser.add_argument("--assignee", help="Assignee gid, me, exact cached user name, or exact cached email")
    update_task_parser.add_argument("--notes")
    update_task_parser.add_argument("--html-notes")
    update_task_parser.add_argument("--due-on")
    update_task_parser.add_argument("--due-at")
    update_task_parser.add_argument("--completed", type=parse_bool)
    update_task_parser.add_argument("--custom-field", action="append", default=[], help="Custom field as gid=value")
    add_common_output_flags(update_task_parser)
    update_task_parser.set_defaults(func=command_update_task)

    comment_parser = subparsers.add_parser("comment-task", help="Create a task story/comment")
    comment_parser.add_argument("task_gid")
    comment_parser.add_argument("--text", help="Plain-text comment body")
    comment_parser.add_argument("--text-file", help="Read plain-text comment body from file")
    comment_parser.add_argument("--html-text", help="Rich-text HTML comment body")
    comment_parser.add_argument("--html-text-file", help="Read rich-text HTML comment body from file")
    add_common_output_flags(comment_parser)
    comment_parser.set_defaults(func=command_comment_task)

    update_story_parser = subparsers.add_parser("update-story", help="Update an existing story/comment")
    update_story_parser.add_argument("story_gid")
    update_story_parser.add_argument("--text", help="Plain-text comment body")
    update_story_parser.add_argument("--text-file", help="Read plain-text comment body from file")
    update_story_parser.add_argument("--html-text", help="Rich-text HTML comment body")
    update_story_parser.add_argument("--html-text-file", help="Read rich-text HTML comment body from file")
    add_common_output_flags(update_story_parser)
    update_story_parser.set_defaults(func=command_update_story)

    task_stories_parser = subparsers.add_parser("task-stories", help="List stories/comments on a task")
    task_stories_parser.add_argument("task_gid")
    task_stories_parser.add_argument("--opt-fields", help="Override story fields")
    task_stories_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    task_stories_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(task_stories_parser)
    task_stories_parser.set_defaults(func=command_task_stories)

    task_comments_parser = subparsers.add_parser("task-comments", help="List only comment stories, including text and html_text")
    task_comments_parser.add_argument("task_gid")
    task_comments_parser.add_argument("--opt-fields", help="Override story fields")
    task_comments_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    task_comments_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(task_comments_parser)
    task_comments_parser.set_defaults(func=command_task_comments)

    task_projects_parser = subparsers.add_parser("task-projects", help="List projects a task belongs to")
    task_projects_parser.add_argument("task_gid")
    task_projects_parser.add_argument("--opt-fields", help="Override project fields")
    add_common_output_flags(task_projects_parser)
    task_projects_parser.set_defaults(func=command_task_projects)

    add_task_project_parser = subparsers.add_parser("add-task-project", help="Add or move a task within a project/section")
    add_task_project_parser.add_argument("task_gid")
    add_task_project_parser.add_argument("project_gid")
    add_task_project_parser.add_argument("--section", help="Section GID for placement")
    add_task_project_parser.add_argument("--insert-before", help="Anchor task GID or literal null")
    add_task_project_parser.add_argument("--insert-after", help="Anchor task GID or literal null")
    add_common_output_flags(add_task_project_parser)
    add_task_project_parser.set_defaults(func=command_add_task_project)

    remove_task_project_parser = subparsers.add_parser("remove-task-project", help="Remove a task from a project")
    remove_task_project_parser.add_argument("task_gid")
    remove_task_project_parser.add_argument("project_gid")
    add_common_output_flags(remove_task_project_parser)
    remove_task_project_parser.set_defaults(func=command_remove_task_project)

    add_task_followers_parser = subparsers.add_parser("add-task-followers", help="Add followers to a task")
    add_task_followers_parser.add_argument("task_gid")
    add_task_followers_parser.add_argument("followers", nargs="+", help="Follower gids, me, exact cached user names/emails; comma-separated values allowed")
    add_common_output_flags(add_task_followers_parser)
    add_task_followers_parser.set_defaults(func=command_add_task_followers)

    remove_task_followers_parser = subparsers.add_parser("remove-task-followers", help="Remove followers from a task")
    remove_task_followers_parser.add_argument("task_gid")
    remove_task_followers_parser.add_argument("followers", nargs="+", help="Follower gids, me, exact cached user names/emails; comma-separated values allowed")
    add_common_output_flags(remove_task_followers_parser)
    remove_task_followers_parser.set_defaults(func=command_remove_task_followers)

    tags_parser = subparsers.add_parser("tags", help="List tags in a workspace")
    tags_parser.add_argument("--workspace", help="Workspace GID override")
    tags_parser.add_argument("--opt-fields", help="Override tag fields")
    tags_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    tags_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(tags_parser)
    tags_parser.set_defaults(func=command_tags)

    create_tag_parser = subparsers.add_parser("create-tag", help="Create a tag")
    create_tag_parser.add_argument("--name", required=True)
    create_tag_parser.add_argument("--workspace", help="Workspace GID override")
    create_tag_parser.add_argument("--color", help="Tag color")
    create_tag_parser.add_argument("--notes")
    add_common_output_flags(create_tag_parser)
    create_tag_parser.set_defaults(func=command_create_tag)

    workspace_custom_fields_parser = subparsers.add_parser("workspace-custom-fields", help="List custom fields in a workspace")
    workspace_custom_fields_parser.add_argument("--workspace", help="Workspace GID override")
    workspace_custom_fields_parser.add_argument("--opt-fields", help="Override field list")
    workspace_custom_fields_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    workspace_custom_fields_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(workspace_custom_fields_parser)
    workspace_custom_fields_parser.set_defaults(func=command_workspace_custom_fields)

    team_custom_fields_parser = subparsers.add_parser("team-custom-fields", help="List team custom field settings")
    team_custom_fields_parser.add_argument("--team", help="Team GID or exact team name from asana-context.json")
    team_custom_fields_parser.add_argument("--opt-fields", help="Override field list")
    team_custom_fields_parser.add_argument("--paginate", action="store_true", help="Follow Asana next_page links")
    team_custom_fields_parser.add_argument("--limit-pages", type=int, default=0, help="Stop pagination after N pages")
    add_common_output_flags(team_custom_fields_parser)
    team_custom_fields_parser.set_defaults(func=command_team_custom_fields)

    project_custom_fields_parser = subparsers.add_parser("project-custom-fields", help="List custom field settings on a project")
    project_custom_fields_parser.add_argument("project_gid")
    project_custom_fields_parser.add_argument("--opt-fields", help="Override field list")
    add_common_output_flags(project_custom_fields_parser)
    project_custom_fields_parser.set_defaults(func=command_project_custom_fields)

    task_custom_fields_parser = subparsers.add_parser("task-custom-fields", help="List custom fields on a task")
    task_custom_fields_parser.add_argument("task_gid")
    task_custom_fields_parser.add_argument("--opt-fields", help="Override field list")
    add_common_output_flags(task_custom_fields_parser)
    task_custom_fields_parser.set_defaults(func=command_task_custom_fields)

    create_custom_field_parser = subparsers.add_parser("create-custom-field", help="Create a workspace custom field")
    create_custom_field_parser.add_argument("--name", required=True)
    create_custom_field_parser.add_argument("--workspace", help="Workspace GID override")
    create_custom_field_parser.add_argument(
        "--resource-subtype",
        required=True,
        help="Asana custom field subtype, e.g. text, number, enum, multi_enum",
    )
    create_custom_field_parser.add_argument("--description")
    create_custom_field_parser.add_argument("--precision", type=int)
    create_custom_field_parser.add_argument("--enum-option", action="append", help="Enum option name; repeat for multiple values")
    add_common_output_flags(create_custom_field_parser)
    create_custom_field_parser.set_defaults(func=command_create_custom_field)

    task_tags_parser = subparsers.add_parser("task-tags", help="List tags on a task")
    task_tags_parser.add_argument("task_gid")
    task_tags_parser.add_argument("--opt-fields", help="Override tag fields")
    add_common_output_flags(task_tags_parser)
    task_tags_parser.set_defaults(func=command_task_tags)

    add_task_tag_parser = subparsers.add_parser("add-task-tag", help="Add a tag to a task")
    add_task_tag_parser.add_argument("task_gid")
    add_task_tag_parser.add_argument("tag_gid")
    add_common_output_flags(add_task_tag_parser)
    add_task_tag_parser.set_defaults(func=command_add_task_tag)

    remove_task_tag_parser = subparsers.add_parser("remove-task-tag", help="Remove a tag from a task")
    remove_task_tag_parser.add_argument("task_gid")
    remove_task_tag_parser.add_argument("tag_gid")
    add_common_output_flags(remove_task_tag_parser)
    remove_task_tag_parser.set_defaults(func=command_remove_task_tag)

    add_task_dependencies_parser = subparsers.add_parser("add-task-dependencies", help="Add dependencies to a task")
    add_task_dependencies_parser.add_argument("task_gid")
    add_task_dependencies_parser.add_argument("dependencies", nargs="+", help="Dependency task gids; comma-separated values allowed")
    add_common_output_flags(add_task_dependencies_parser)
    add_task_dependencies_parser.set_defaults(func=command_add_task_dependencies)

    remove_task_dependencies_parser = subparsers.add_parser("remove-task-dependencies", help="Remove dependencies from a task")
    remove_task_dependencies_parser.add_argument("task_gid")
    remove_task_dependencies_parser.add_argument("dependencies", nargs="+", help="Dependency task gids; comma-separated values allowed")
    add_common_output_flags(remove_task_dependencies_parser)
    remove_task_dependencies_parser.set_defaults(func=command_remove_task_dependencies)

    batch_parser = subparsers.add_parser("batch", help="Run an Asana batch request from a JSON array of actions")
    batch_parser.add_argument("--actions", help="Inline JSON array of batch actions")
    batch_parser.add_argument("--actions-file", help="Path to a JSON file containing a batch actions array")
    add_common_output_flags(batch_parser)
    batch_parser.set_defaults(func=command_batch)

    create_project_parser = subparsers.add_parser("create-project", help="Create a project")
    create_project_parser.add_argument("--name", required=True)
    create_project_parser.add_argument("--team", help="Team GID or exact team name from asana-context.json")
    create_project_parser.add_argument("--workspace", help="Workspace GID override")
    create_project_parser.add_argument("--notes")
    add_common_output_flags(create_project_parser)
    create_project_parser.set_defaults(func=command_create_project)

    update_project_parser = subparsers.add_parser("update-project", help="Update a project")
    update_project_parser.add_argument("project_gid")
    update_project_parser.add_argument("--name")
    update_project_parser.add_argument("--notes")
    update_project_parser.add_argument("--archived", type=parse_bool)
    add_common_output_flags(update_project_parser)
    update_project_parser.set_defaults(func=command_update_project)

    context_parser = subparsers.add_parser("show-context", help="Print local workspace/team defaults")
    add_common_output_flags(context_parser)
    context_parser.set_defaults(func=command_show_context)

    cache_parser = subparsers.add_parser("show-cache", help="Print the local Asana entity cache")
    add_common_output_flags(cache_parser)
    cache_parser.set_defaults(func=command_show_cache)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
