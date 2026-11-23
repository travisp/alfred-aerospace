"""AeroSpace helpers for Alfred workflow scripts."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional

from .alfred_metadata import extract_shortcut_metadata


INSTALL_GUIDE_URL = "https://nikitabobko.github.io/AeroSpace/guide#installation"
MISSING_CONFIG_MESSAGE = (
    "Config file does not exist. Please check the path in preferences."
)

DEFAULT_PATHS = [
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
]

WINDOWS_FORMAT = (
    "%{app-name} %{window-title} %{window-id} %{app-pid} "
    "%{workspace} %{monitor-name}"
)

FOCUSED_WINDOW_FORMAT = (
    "%{app-name} %{window-title} %{window-id} %{app-pid} %{workspace} "
    "%{monitor-name} %{window-layout} "
    "%{window-parent-container-layout} %{workspace-root-container-layout} "
    "%{window-is-fullscreen} %{workspace-is-focused} %{workspace-is-visible} "
    "%{monitor-is-main}"
)

WORKSPACES_FORMAT = "%{workspace} %{monitor-name} %{workspace-is-focused}"


def _ensure_path(env: Dict[str, str]) -> Dict[str, str]:
    current = env.get("PATH", "")
    parts = [p for p in current.split(os.pathsep) if p]
    for path in DEFAULT_PATHS:
        if path not in parts:
            parts.append(path)
    env["PATH"] = os.pathsep.join(parts)
    return env


def _run_command(args: List[str], timeout: int = 15) -> str:
    env = _ensure_path(os.environ.copy())
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or "Command failed.")
    return result.stdout


def get_config_path() -> str:
    path = _run_command(["aerospace", "config", "--config-path"]).strip()
    if not path:
        raise RuntimeError("Unable to resolve AeroSpace config path.")
    return os.path.expanduser(path)


def load_config() -> Dict[str, Any]:
    try:
        path = get_config_path()
    except Exception as exc:  # pylint: disable=broad-except
        return {"error": str(exc), "path": ""}

    if not os.path.exists(path):
        return {"error": MISSING_CONFIG_MESSAGE, "path": path}

    try:
        raw_text = Path(path).read_text(encoding="utf-8")
        config = tomllib.loads(raw_text)
    except Exception as exc:  # pylint: disable=broad-except
        return {"error": f"Failed to parse config: {exc}", "path": path}

    return {"config": config, "path": path, "text": raw_text}


def normalize_description(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=True)
    text = text.replace('"', "")
    return re.sub(r"(?<=\w)-(?=\w)", " ", text)


def shortcut_description(value: Any) -> str:
    if (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, str) for item in value)
        and value[1].strip().lower() == "mode main"
    ):
        return value[0].strip()
    return normalize_description(value)


def fuzzy_score(needle: str, haystack: str) -> Optional[int]:
    if not needle or not haystack:
        return None
    needle = needle.lower()
    haystack = haystack.lower()

    if needle == haystack:
        return 1000
    if haystack.startswith(needle):
        return 700 - len(haystack)
    if needle in haystack:
        return 500 - haystack.index(needle)

    score = 0
    h_idx = 0
    consecutive = 0
    for ch in needle:
        found = haystack.find(ch, h_idx)
        if found == -1:
            return None
        if found == h_idx:
            consecutive += 1
            score += 3 + consecutive
        else:
            consecutive = 0
            score += 1
        h_idx = found + 1

    score -= max(0, h_idx - len(needle))
    return score


def filter_windows(windows: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    if not query:
        return windows
    query = query.lower()
    ranked: List[tuple[int, int, int, Dict[str, Any]]] = []
    for idx, window in enumerate(windows):
        app_name = str(window.get("app-name", ""))
        window_title = str(window.get("window-title", ""))
        app_score = fuzzy_score(query, app_name)
        if app_score is not None:
            ranked.append((0, -app_score, idx, window))
            continue
        title_score = fuzzy_score(query, window_title)
        if title_score is not None:
            ranked.append((1, -title_score, idx, window))

    ranked.sort()
    return [entry[3] for entry in ranked]


def extract_shortcuts(config: Dict[str, Any], config_text: str) -> List[Dict[str, str]]:
    shortcuts: List[Dict[str, str]] = []
    modes = config.get("mode", {})
    if not isinstance(modes, dict):
        return shortcuts
    shortcut_metadata = extract_shortcut_metadata(config_text)

    for mode_name, mode_config in modes.items():
        if not isinstance(mode_config, dict):
            continue
        bindings = mode_config.get("binding", {})
        if not isinstance(bindings, dict):
            continue

        mode = str(mode_name)
        for shortcut, command in bindings.items():
            binding = str(shortcut)
            metadata = shortcut_metadata.get((mode, binding), {})
            if metadata.get("skip"):
                continue
            normalized_command = normalize_description(command)
            shortcuts.append(
                {
                    "mode": mode,
                    "shortcut": binding,
                    "description": metadata.get("name", shortcut_description(command)),
                    "command": normalized_command,
                }
            )
    return shortcuts


def _escape_applescript(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def display_notification(message: str, title: str = "AeroSpace") -> None:
    if not message:
        return
    script = (
        'display notification "'
        + _escape_applescript(message)
        + '" with title "'
        + _escape_applescript(title)
        + '"'
    )
    try:
        subprocess.run(["osascript", "-e", script], check=False)
    except Exception:  # pylint: disable=broad-except
        return


def notify_error(message: str) -> None:
    normalized = " ".join(str(message).split()).strip()
    if not normalized:
        normalized = "Unknown error."
    display_notification(normalized, title="AeroSpace Error")


def trigger_binding(binding: str, mode: str) -> str:
    output = _run_command(["aerospace", "trigger-binding", binding, "--mode", mode])
    return output.strip()


def run_aerospace_command(command: str) -> str:
    args = shlex.split(command.strip())
    if not args:
        raise RuntimeError("Command is empty.")

    output = _run_command(["aerospace", *args])
    return output.strip()


def _add_window_app_paths(windows: List[Dict[str, Any]]) -> None:
    pids = {window["app-pid"] for window in windows}
    if not pids:
        return

    # lsappinfo accepts multiple info queries in one invocation.
    args = ["/usr/bin/lsappinfo"]
    for pid in pids:
        args.extend(["info", "-only", "pid,bundlepath", str(pid)])
    try:
        output = _run_command(args, timeout=1)
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return  # Icons are optional; keep the window results.

    paths: Dict[int, str] = {}
    for record in output.split("\n\n"):
        pid_match = re.search(r"^[ \t]+pid = (\d+)\b", record, re.MULTILINE)
        path_match = re.search(r'^[ \t]+bundle path="(.+)"[ \t]*$', record, re.MULTILINE)
        if pid_match and path_match:
            paths[int(pid_match[1])] = path_match[1]

    for window in windows:
        window["app-path"] = paths.get(window["app-pid"])


def list_windows(scope: str) -> List[Dict[str, Any]]:
    args = [
        "aerospace",
        "list-windows",
        "--json",
        "--format",
        WINDOWS_FORMAT,
    ]
    if scope == "all":
        args.append("--all")
    else:
        args.extend(["--workspace", "focused"])

    windows = json.loads(_run_command(args))
    _add_window_app_paths(windows)
    return windows


def get_focused_window() -> Optional[Dict[str, Any]]:
    output = _run_command(
        [
            "aerospace",
            "list-windows",
            "--focused",
            "--json",
            "--format",
            FOCUSED_WINDOW_FORMAT,
        ]
    )
    windows = json.loads(output)
    if not windows:
        return None

    window = windows[0]
    _add_window_app_paths([window])
    return window


def list_workspaces() -> List[Dict[str, Any]]:
    output = _run_command(
        [
            "aerospace",
            "list-workspaces",
            "--all",
            "--json",
            "--format",
            WORKSPACES_FORMAT,
        ]
    )
    workspaces = json.loads(output)
    if not isinstance(workspaces, list):
        return []
    return workspaces


def focus_window(window_id: str) -> None:
    _run_command(["aerospace", "focus", "--window-id", str(window_id)])


def set_layout(window_id: int, layout: str) -> None:
    _run_command(["aerospace", "layout", "--window-id", str(window_id), layout])
