#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import extract_shortcuts, load_config


ALWAYS_AVAILABLE_COMMANDS = [
    "balance-sizes",
    "workspace-back-and-forth",
    "flatten-workspace-tree",
    "reload-config",
    "fullscreen --no-outer-gaps",
    "layout tiling floating",
]


def _bound_commands(config: dict[str, Any]) -> set[str]:
    commands: set[str] = set()
    modes = config.get("mode", {})
    if not isinstance(modes, dict):
        return commands

    for mode_config in modes.values():
        if not isinstance(mode_config, dict):
            continue
        bindings = mode_config.get("binding", {})
        if not isinstance(bindings, dict):
            continue
        for binding_value in bindings.values():
            values = (
                binding_value if isinstance(binding_value, list) else [binding_value]
            )
            for command in values:
                if isinstance(command, str):
                    normalized = command.strip()
                    if normalized:
                        commands.add(normalized)
    return commands


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if not query:
        query = sys.stdin.read().strip()

    result = load_config()
    if "error" in result:
        items = [
            {
                "title": "AeroSpace config error",
                "subtitle": result["error"],
                "valid": False,
            }
        ]
        print(json.dumps({"items": items}))
        return

    shortcuts = extract_shortcuts(result["config"])
    bound_commands = _bound_commands(result["config"])
    unbound_always_commands = [
        command
        for command in ALWAYS_AVAILABLE_COMMANDS
        if command not in bound_commands
    ]

    items = []
    query_lower = query.lower()
    for shortcut in shortcuts:
        title = shortcut["description"]
        subtitle = f"{shortcut['shortcut']} - mode: {shortcut['mode']}"
        match_text = f"{title} {shortcut['shortcut']} {shortcut['mode']}"
        if query_lower and query_lower not in match_text.lower():
            continue
        items.append(
            {
                "title": title,
                "subtitle": subtitle,
                "arg": shortcut["shortcut"],
                "uid": f"shortcut:{shortcut['mode']}:{shortcut['shortcut']}",
                "match": match_text,
            }
        )

    for command in unbound_always_commands:
        title = " ".join(command.replace("-", " ").split())
        subtitle = "no bound shortcut"
        match_text = f"{title} {command} no bound shortcut"
        if query_lower and query_lower not in match_text.lower():
            continue
        items.append(
            {
                "title": title,
                "subtitle": subtitle,
                "arg": f"command:{command}",
                "uid": f"command:{command.replace(' ', '_')}",
                "match": match_text,
            }
        )

    print(json.dumps({"items": items}))


if __name__ == "__main__":
    main()
