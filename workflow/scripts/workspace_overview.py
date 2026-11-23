#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import filter_windows, fuzzy_score, list_windows, list_workspaces


def _workspace_item(ws: dict, windows: list[dict], show_monitor: bool) -> dict:
    workspace = str(ws.get("workspace", ""))
    focused = str(ws.get("workspace-is-focused", "")).lower() == "true"
    monitor = str(ws.get("monitor-name", "")).strip()
    subtitle = [f"{len(windows)} windows"]
    if focused:
        subtitle.append("focused")
    if show_monitor and monitor:
        subtitle.append(monitor)

    app_names = []
    for window in windows:
        name = str(window.get("app-name", "")).strip()
        if name and name not in app_names:
            app_names.append(name)
    if app_names:
        preview = ", ".join(app_names[:3])
        if len(app_names) > 3:
            preview += f" +{len(app_names) - 3}"
        subtitle.append(f"apps {preview}")

    return {
        "title": f"Workspace {workspace}{' [focused]' if focused else ''}",
        "subtitle": " | ".join(subtitle),
        "valid": False,
    }


def _window_item(window: dict) -> dict:
    item: dict[str, Any] = {
        "title": str(window.get("app-name", "Unknown")),
        "subtitle": str(window.get("window-title", "")).strip(),
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

    workspaces_by_id = {str(ws.get("workspace", "")): ws for ws in workspaces}
    monitor_names = {
        str(ws.get("monitor-name", "")).strip() for ws in workspaces
    }
    monitor_names.discard("")
    show_monitor = len(monitor_names) > 1
    grouped: dict[str, list] = {}
    for window in windows:
        workspace = str(window.get("workspace", ""))
        grouped.setdefault(workspace, []).append(window)

    if workspace_query and workspace_query in workspaces_by_id:
        windows_in_workspace = filter_windows(
            grouped.get(workspace_query, []), filter_query
        )
        items = [
            _workspace_item(
                workspaces_by_id[workspace_query], windows_in_workspace, show_monitor
            )
        ]
        items.extend(_window_item(window) for window in windows_in_workspace)
        if not windows_in_workspace:
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
    for workspace, ws in workspaces_by_id.items():
        if workspace_query and fuzzy_score(workspace_query, workspace) is None:
            continue
        item = _workspace_item(ws, grouped.get(workspace, []), show_monitor)
        item["autocomplete"] = f"{workspace} "
        items.append(item)

    if not items:
        items = [{"title": "No workspaces found", "valid": False}]

    print(json.dumps({"items": items}))


if __name__ == "__main__":
    main()
