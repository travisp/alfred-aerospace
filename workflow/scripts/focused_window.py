#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import get_focused_window


LAYOUT_OPTIONS = [
    "h_tiles",
    "v_tiles",
    "h_accordion",
    "v_accordion",
    "tiles",
    "accordion",
    "horizontal",
    "vertical",
    "tiling",
    "floating",
]


def _file_icon(path_value: str | None) -> dict | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.exists():
        return None
    return {"type": "fileicon", "path": str(path)}


def _normalize_query(query: str) -> str:
    tokens = [
        token
        for token in query.lower().split()
        if token not in {"set", "layout", "to"}
    ]
    return " ".join(tokens).strip()


def _parse_layout_state(current_layout: str) -> tuple[str | None, str | None]:
    if not current_layout:
        return None, None
    if current_layout == "floating":
        return "floating", None
    if current_layout in {"tiles", "tiling"}:
        return "tiles", None
    if current_layout == "accordion":
        return "accordion", None
    if current_layout == "horizontal":
        return None, "horizontal"
    if current_layout == "vertical":
        return None, "vertical"
    if current_layout.startswith("h_"):
        return current_layout.replace("h_", "", 1), "horizontal"
    if current_layout.startswith("v_"):
        return current_layout.replace("v_", "", 1), "vertical"
    return None, None


def _ordered_layout_options(current_layout: str) -> list[str]:
    layout_type, _ = _parse_layout_state(current_layout)
    if layout_type == "tiles":
        return ["h_tiles", "v_tiles", "h_accordion", "v_accordion"]
    if layout_type == "accordion":
        return ["h_accordion", "v_accordion", "h_tiles", "v_tiles"]
    return ["h_tiles", "v_tiles", "h_accordion", "v_accordion"]


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if not query:
        query = sys.stdin.read().strip()

    window = None
    try:
        window = get_focused_window()
    except Exception as exc:  # pylint: disable=broad-except
        items = [
            {
                "title": "Unable to get focused window",
                "subtitle": str(exc),
                "valid": False,
            }
        ]
        print(json.dumps({"items": items}))
        return

    if not window:
        items = [{"title": "No focused window", "valid": False}]
        print(json.dumps({"items": items}))
        return

    app_name = str(window.get("app-name", "Unknown"))
    window_title = str(window.get("window-title", "")).strip()
    window_layout = str(window.get("window-layout", "")).strip()
    parent_layout = str(window.get("window-parent-container-layout", "")).strip()
    root_layout = str(window.get("workspace-root-container-layout", "")).strip()
    is_fullscreen = str(window.get("window-is-fullscreen", "")).lower() == "true"

    items: list[dict[str, Any]] = []
    icon = _file_icon(window.get("app-path"))

    details_parts = []
    if window_layout:
        details_parts.append(f"layout {window_layout}")
    if parent_layout:
        details_parts.append(f"parent {parent_layout}")
    if root_layout:
        details_parts.append(f"root {root_layout}")
    if is_fullscreen:
        details_parts.append("fullscreen")

    subtitle = ""
    if window_title and details_parts:
        subtitle = f"{window_title} — {' | '.join(details_parts)}"
    elif window_title:
        subtitle = window_title
    elif details_parts:
        subtitle = " | ".join(details_parts)

    header_item: dict[str, Any] = {
        "title": app_name,
        "subtitle": subtitle,
        "valid": False,
    }
    if icon:
        header_item["icon"] = icon
    items.append(header_item)

    current_layout = window_layout
    layout_actions = []
    filter_query = _normalize_query(query)

    toggle_action = None
    if current_layout == "floating":
        toggle_action = {
            "title": "Set layout: tiling",
            "subtitle": "Switch from floating",
            "arg": "tiling",
            "autocomplete": "tiling",
        }
    else:
        toggle_action = {
            "title": "Set layout: floating",
            "subtitle": "Switch from tiling",
            "arg": "floating",
            "autocomplete": "floating",
        }

    options = _ordered_layout_options(current_layout)
    for layout in options:
        if layout == current_layout:
            continue
        action = {
            "title": f"Set layout: {layout}",
            "subtitle": f"Current: {current_layout}" if current_layout else "",
            "arg": layout,
            "autocomplete": layout,
        }
        if filter_query:
            label = layout.lower()
            if filter_query not in label:
                continue
        layout_actions.append(action)

    if toggle_action:
        if not filter_query or filter_query in toggle_action["title"].lower():
            layout_actions.append(toggle_action)

    if layout_actions:
        items.extend(layout_actions)
    else:
        items.append(
            {
                "title": "No layout changes available",
                "valid": False,
            }
        )

    print(json.dumps({"items": items}))


if __name__ == "__main__":
    main()
