#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import filter_windows, fuzzy_score, list_windows, list_workspaces


def _window_item(window: dict, include_workspace: bool, include_monitor: bool = True) -> dict:
    app_name = str(window.get("app-name", "Unknown"))
    window_title = str(window.get("window-title", "")).strip()
    workspace = str(window.get("workspace", "")).strip()
    monitor = str(window.get("monitor-name", "")).strip()

    subtitle_parts = []
    if include_workspace and workspace:
        subtitle_parts.append(f"ws {workspace}")
    if include_monitor and monitor:
        subtitle_parts.append(monitor)
    if window_title:
        subtitle_parts.append(window_title)

    subtitle = " - ".join(subtitle_parts)
    item: dict[str, Any] = {
        "title": app_name,
        "subtitle": subtitle,
        "arg": str(window.get("window-id", "")),
        "uid": f"window:{window.get('window-id', '')}",
    }
    app_path = window.get("app-path")
    if app_path:
        path = Path(str(app_path))
        if path.exists():
            item["icon"] = {"type": "fileicon", "path": str(path)}
    return item


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if not query:
        query = sys.stdin.read().strip()

    cleaned = query.strip()
    if cleaned.lower().startswith("ws "):
        cleaned = cleaned[3:].strip()
    if cleaned.lower().startswith("workspace "):
        cleaned = cleaned[10:].strip()

    workspace_query = ""
    filter_query = ""
    if cleaned:
        parts = cleaned.split(maxsplit=1)
        workspace_query = parts[0]
        if len(parts) > 1:
            filter_query = parts[1]

    try:
        windows = list_windows("all")
    except Exception as exc:  # pylint: disable=broad-except
        items = [
            {
                "title": "Unable to list windows",
                "subtitle": str(exc),
                "valid": False,
            }
        ]
        print(json.dumps({"items": items}))
        return

    try:
        workspaces = list_workspaces()
    except Exception as exc:  # pylint: disable=broad-except
        items = [
            {
                "title": "Unable to list workspaces",
                "subtitle": str(exc),
                "valid": False,
            }
        ]
        print(json.dumps({"items": items}))
        return

    workspace_ids = {str(ws.get("workspace", "")) for ws in workspaces}
    monitor_names = {
        str(ws.get("monitor-name", "")).strip() for ws in workspaces
    }
    monitor_names.discard("")
    show_monitor = len(monitor_names) > 1
    grouped: dict[str, list] = {}
    for window in windows:
        workspace = str(window.get("workspace", ""))
        grouped.setdefault(workspace, []).append(window)

    if workspace_query and workspace_query in workspace_ids:
        windows_in_workspace = grouped.get(workspace_query, [])
        if filter_query:
            windows_in_workspace = filter_windows(windows_in_workspace, filter_query)

        ws_meta = next(
            (
                ws
                for ws in workspaces
                if str(ws.get("workspace", "")) == workspace_query
            ),
            None,
        )
        monitor = str(ws_meta.get("monitor-name", "")).strip() if ws_meta else ""
        focused = (
            str(ws_meta.get("workspace-is-focused", "")).lower() == "true"
            if ws_meta
            else False
        )
        visible = (
            str(ws_meta.get("workspace-is-visible", "")).lower() == "true"
            if ws_meta
            else False
        )

        state = "focused" if focused else ""

        app_names = []
        for window in windows_in_workspace:
            name = str(window.get("app-name", "")).strip()
            if name and name not in app_names:
                app_names.append(name)
        preview = ""
        if app_names:
            preview_items = app_names[:3]
            preview = ", ".join(preview_items)
            if len(app_names) > 3:
                preview = f"{preview} +{len(app_names) - 3}"

        subtitle_parts = [f"{len(windows_in_workspace)} windows"]
        if state:
            subtitle_parts.append(state)
        if show_monitor and monitor:
            subtitle_parts.append(monitor)
        if preview:
            subtitle_parts.append(f"apps {preview}")

        items = [
            {
                "title": f"Workspace {workspace_query}{' [focused]' if focused else ''}",
                "subtitle": " | ".join(subtitle_parts),
                "valid": False,
            }
        ]
        items.extend(
            _window_item(window, include_workspace=False, include_monitor=False)
            for window in windows_in_workspace
        )
        if len(items) == 1:
            items.append(
                {
                    "title": f"No windows in workspace {workspace_query}",
                    "valid": False,
                }
            )
        print(json.dumps({"items": items}))
        return

    items = []
    if not cleaned:
        items.append(
            {
                "title": "Type a workspace id to list its windows",
                "subtitle": "Example: 2 or ws 2 chrome",
                "valid": False,
            }
        )
    for ws in workspaces:
        workspace = str(ws.get("workspace", ""))
        if workspace_query:
            score = fuzzy_score(workspace_query, workspace)
            if score is None:
                continue
        monitor = str(ws.get("monitor-name", "")).strip()
        focused = str(ws.get("workspace-is-focused", "")).lower() == "true"
        visible = str(ws.get("workspace-is-visible", "")).lower() == "true"

        state = "focused" if focused else ""

        windows_in_workspace = grouped.get(workspace, [])
        window_count = len(windows_in_workspace)

        app_names = []
        for window in windows_in_workspace:
            name = str(window.get("app-name", "")).strip()
            if name and name not in app_names:
                app_names.append(name)
        preview = ""
        if app_names:
            preview_items = app_names[:3]
            preview = ", ".join(preview_items)
            if len(app_names) > 3:
                preview = f"{preview} +{len(app_names) - 3}"

        subtitle_parts = [f"{window_count} windows"]
        if state:
            subtitle_parts.append(state)
        if show_monitor and monitor:
            subtitle_parts.append(monitor)
        if preview:
            subtitle_parts.append(f"apps {preview}")

        items.append(
            {
                "title": f"Workspace {workspace}{' [focused]' if focused else ''}",
                "subtitle": " | ".join(subtitle_parts),
                "valid": False,
                "autocomplete": f"{workspace} ",
            }
        )

    if not items:
        items = [{"title": "No workspaces found", "valid": False}]

    print(json.dumps({"items": items}))


if __name__ == "__main__":
    main()
