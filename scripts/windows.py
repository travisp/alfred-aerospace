#!/usr/bin/env python3

import json
import os
import sys
import time
from typing import Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import list_windows


def _cache_path(scope: str) -> Path | None:
    cache_root = os.environ.get("alfred_workflow_cache")
    if not cache_root:
        return None
    return Path(cache_root) / f"windows_{scope}.json"


def _load_cache(path: Path, ttl_seconds: float) -> list | None:
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl_seconds:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # pylint: disable=broad-except
        return None


def _save_cache(path: Path, windows: list) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(windows), encoding="utf-8")
    except Exception:  # pylint: disable=broad-except
        return


def _filter_windows(windows: list, query: str) -> list:
    if not query:
        return windows
    query = query.lower()
    app_matches = []
    title_matches = []
    for window in windows:
        app_name = str(window.get("app-name", "")).lower()
        if app_name.startswith(query):
            app_matches.append(window)
            continue
        window_title = str(window.get("window-title", "")).lower()
        if window_title.startswith(query):
            title_matches.append(window)
    return app_matches + title_matches


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if not query:
        query = sys.stdin.read().strip()
    scope_arg = sys.argv[2] if len(sys.argv) > 2 else ""
    scope = scope_arg.lower() if scope_arg else os.environ.get("scope", "focused").lower()
    if scope not in {"focused", "all"}:
        scope = "focused"

    cache_file = _cache_path(scope)
    windows = None
    if cache_file:
        windows = _load_cache(cache_file, ttl_seconds=1.5)

    if windows is None:
        try:
            windows = list_windows(scope)
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
        if cache_file:
            _save_cache(cache_file, windows)

    windows = _filter_windows(windows, query)
    if not windows:
        items = [
            {
                "title": "No windows found",
                "valid": False,
            }
        ]
        print(json.dumps({"items": items}))
        return

    items = []
    for window in windows:
        app_name = str(window.get("app-name", "Unknown"))
        window_title = str(window.get("window-title", "")).strip()
        workspace = str(window.get("workspace", "")).strip()
        monitor = str(window.get("monitor-name", "")).strip()
        context_parts = []
        if workspace:
            context_parts.append(f"ws {workspace}")
        if monitor:
            context_parts.append(monitor)

        subtitle_parts = []
        if window_title:
            subtitle_parts.append(window_title)
        if context_parts:
            subtitle_parts.append(" | ".join(context_parts))
        subtitle = " - ".join(subtitle_parts)

        item: dict[str, Any] = {
            "title": app_name,
            "subtitle": subtitle,
            "arg": str(window.get("window-id", "")),
            "uid": f"window:{window.get('window-id', '')}",
        }
        app_path = window.get("app-path")
        if app_path:
            item["icon"] = {"path": app_path}
        items.append(item)

    print(json.dumps({"items": items}))


if __name__ == "__main__":
    main()
