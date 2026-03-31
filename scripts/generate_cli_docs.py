#!/usr/bin/env python3
"""
Generate parser-derived CLI reference files for scripts/asana_api.py.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
MODULE_PATH = SCRIPT_DIR / "asana_api.py"
MARKDOWN_OUTPUT = REPO_ROOT / "references" / "cli-reference.md"
JSON_OUTPUT = REPO_ROOT / "references" / "cli-reference.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CLI reference docs from scripts/asana_api.py")
    parser.add_argument("--markdown-out", type=Path, default=MARKDOWN_OUTPUT, help="Path to write the generated Markdown reference")
    parser.add_argument("--json-out", type=Path, default=JSON_OUTPUT, help="Path to write the generated JSON reference")
    parser.add_argument("--check", action="store_true", help="Fail instead of writing when generated output differs from the target files")
    return parser.parse_args()


def load_asana_api_module() -> Any:
    spec = importlib.util.spec_from_file_location("asana_api", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().split())


def json_safe(value: Any) -> Any:
    if value is argparse.SUPPRESS:
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, set):
        return [json_safe(item) for item in sorted(value, key=repr)]
    if hasattr(value, "__name__"):
        return value.__name__
    return repr(value)


def iter_subparser_choices(parser: argparse.ArgumentParser) -> tuple[argparse._SubParsersAction[Any], dict[str, str]]:  # type: ignore[attr-defined]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):  # type: ignore[attr-defined]
            help_map = {
                choice_action.dest: normalize_text(choice_action.help)
                for choice_action in action._get_subactions()
            }
            return action, help_map
    raise RuntimeError("Expected at least one subparser on the Asana CLI")


def action_kind(action: argparse.Action) -> str:
    if not action.option_strings:
        return "positional"
    if action.nargs == 0:
        return "flag"
    return "option"


def metavar_for_action(action: argparse.Action) -> str:
    metavar = action.metavar
    if isinstance(metavar, tuple):
        return " ".join(str(item) for item in metavar)
    if metavar is not None:
        return str(metavar)
    if action.option_strings:
        return action.dest.upper()
    return action.dest


def format_usage(parser: argparse.ArgumentParser) -> str:
    usage = parser.format_usage().strip()
    return normalize_text(usage)


def extract_action_spec(action: argparse.Action) -> dict[str, Any] | None:
    if isinstance(action, argparse._HelpAction):  # type: ignore[attr-defined]
        return None
    if action.help is argparse.SUPPRESS:
        return None

    spec: dict[str, Any] = {
        "kind": action_kind(action),
        "dest": action.dest,
        "help": normalize_text(action.help),
        "metavar": metavar_for_action(action),
        "nargs": json_safe(action.nargs),
        "required": bool(getattr(action, "required", False) or not action.option_strings),
        "default": json_safe(action.default),
        "choices": json_safe(list(action.choices)) if action.choices is not None else None,
        "type": json_safe(getattr(action, "type", None)),
    }

    if action.option_strings:
        spec["option_strings"] = list(action.option_strings)
    else:
        spec["name"] = action.dest
    return spec


def option_signature(option: dict[str, Any]) -> str:
    stable_fields = {
        "kind": option["kind"],
        "dest": option["dest"],
        "metavar": option["metavar"],
        "nargs": option["nargs"],
        "required": option["required"],
        "choices": option["choices"],
        "type": option["type"],
        "help": option["help"],
        "option_strings": option["option_strings"],
    }
    return json.dumps(stable_fields, sort_keys=True)


def build_reference_payload() -> dict[str, Any]:
    module = load_asana_api_module()
    parser = module.build_parser()
    subparsers_action, help_map = iter_subparser_choices(parser)

    commands: list[dict[str, Any]] = []
    for command_name, subparser in subparsers_action.choices.items():
        subparser.prog = f"asana_api.py {command_name}"
        positionals: list[dict[str, Any]] = []
        options: list[dict[str, Any]] = []
        for action in subparser._actions:
            spec = extract_action_spec(action)
            if spec is None:
                continue
            if spec["kind"] == "positional":
                positionals.append(spec)
            else:
                options.append(spec)

        commands.append(
            {
                "name": command_name,
                "summary": help_map.get(command_name, ""),
                "usage": format_usage(subparser),
                "positionals": positionals,
                "options": options,
            }
        )

    signature_counts: dict[str, int] = {}
    signature_to_option: dict[str, dict[str, Any]] = {}
    for command in commands:
        seen_signatures = set()
        for option in command["options"]:
            signature = option_signature(option)
            signature_to_option[signature] = option
            seen_signatures.add(signature)
        for signature in seen_signatures:
            signature_counts[signature] = signature_counts.get(signature, 0) + 1

    shared_signatures = {
        signature
        for signature, count in signature_counts.items()
        if count == len(commands)
    }
    shared_options = [
        signature_to_option[signature]
        for signature in sorted(shared_signatures)
    ]

    for command in commands:
        command["options"] = [
            option for option in command["options"] if option_signature(option) not in shared_signatures
        ]
        command["includes_shared_options"] = bool(shared_options)

    return {
        "source": "scripts/asana_api.py",
        "generator": "scripts/generate_cli_docs.py",
        "parser_description": normalize_text(parser.description),
        "shared_options": shared_options,
        "commands": commands,
    }


def format_option_display(option: dict[str, Any]) -> str:
    pieces = ["`" + "`, `".join(option["option_strings"]) + "`"]
    if option["kind"] == "option":
        pieces.append(f"`{option['metavar']}`")
    return " ".join(pieces)


def format_positional_display(positional: dict[str, Any]) -> str:
    label = positional["metavar"]
    if positional["nargs"] == "+":
        label = f"{label}..."
    return f"`{label}`"


def format_choices(option: dict[str, Any]) -> str:
    choices = option.get("choices")
    if not choices:
        return ""
    return ", ".join(f"`{choice}`" for choice in choices)


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Asana API CLI Reference",
        "",
        f"Generated from `{payload['source']}` by `{payload['generator']}`. Do not edit manually.",
        "",
        f"- CLI: {payload['parser_description']}",
        f"- Commands: {len(payload['commands'])}",
        "",
        "## Command Index",
        "",
        "| Command | Summary |",
        "| --- | --- |",
    ]

    for command in payload["commands"]:
        lines.append(f"| `{command['name']}` | {command['summary']} |")

    if payload["shared_options"]:
        lines.extend(
            [
                "",
                "## Shared Options",
                "",
                "These options are available on every subcommand.",
                "",
                "| Option | Kind | Description | Choices |",
                "| --- | --- | --- | --- |",
            ]
        )
        for option in payload["shared_options"]:
            lines.append(
                "| "
                f"{format_option_display(option)} | "
                f"{option['kind']} | "
                f"{option['help'] or ''} | "
                f"{format_choices(option)} |"
            )

    for command in payload["commands"]:
        lines.extend(
            [
                "",
                f"## `{command['name']}`",
                "",
                f"- Summary: {command['summary']}",
                f"- Usage: `{command['usage']}`",
            ]
        )
        if command["includes_shared_options"]:
            lines.append("- Shared options: see [Shared Options](#shared-options)")

        if command["positionals"]:
            lines.extend(
                [
                    "",
                    "### Positional Arguments",
                    "",
                    "| Argument | Required | Description |",
                    "| --- | --- | --- |",
                ]
            )
            for positional in command["positionals"]:
                lines.append(
                    "| "
                    f"{format_positional_display(positional)} | "
                    f"{'yes' if positional['required'] else 'no'} | "
                    f"{positional['help'] or ''} |"
                )

        if command["options"]:
            lines.extend(
                [
                    "",
                    "### Command Options",
                    "",
                    "| Option | Kind | Required | Description | Choices |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for option in command["options"]:
                lines.append(
                    "| "
                    f"{format_option_display(option)} | "
                    f"{option['kind']} | "
                    f"{'yes' if option['required'] else 'no'} | "
                    f"{option['help'] or ''} | "
                    f"{format_choices(option)} |"
                )
        else:
            lines.extend(["", "### Command Options", "", "No command-specific options."])

    return "\n".join(lines) + "\n"


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_or_check(path: Path, expected: str, check: bool) -> bool:
    current = path.read_text() if path.exists() else None
    if current == expected:
        return False
    if check:
        raise SystemExit(f"{path} is out of date. Run: python3 scripts/generate_cli_docs.py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected)
    return True


def main() -> None:
    args = parse_args()
    payload = build_reference_payload()
    markdown = render_markdown(payload)
    json_output = render_json(payload)

    markdown_changed = write_or_check(args.markdown_out, markdown, args.check)
    json_changed = write_or_check(args.json_out, json_output, args.check)

    if args.check:
        print("cli-docs: up to date")
        return

    changed_paths = []
    if markdown_changed:
        changed_paths.append(str(args.markdown_out.relative_to(REPO_ROOT)))
    if json_changed:
        changed_paths.append(str(args.json_out.relative_to(REPO_ROOT)))
    if changed_paths:
        print("cli-docs: wrote " + ", ".join(changed_paths))
    else:
        print("cli-docs: no changes")


if __name__ == "__main__":
    main()
