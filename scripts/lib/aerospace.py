"""AeroSpace helpers for Alfred workflow scripts."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional


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

MODIFIER_MAP = {
    "cmd": "command down",
    "command": "command down",
    "ctrl": "control down",
    "control": "control down",
    "alt": "option down",
    "option": "option down",
    "shift": "shift down",
}

KEYCODE_MAP = {
    "a": 0,
    "s": 1,
    "d": 2,
    "f": 3,
    "h": 4,
    "g": 5,
    "z": 6,
    "x": 7,
    "c": 8,
    "v": 9,
    "iso_section": 10,
    "b": 11,
    "q": 12,
    "w": 13,
    "e": 14,
    "r": 15,
    "y": 16,
    "t": 17,
    "1": 18,
    "2": 19,
    "3": 20,
    "4": 21,
    "6": 22,
    "5": 23,
    "equal": 24,
    "9": 25,
    "7": 26,
    "minus": 27,
    "8": 28,
    "0": 29,
    "right_bracket": 30,
    "o": 31,
    "u": 32,
    "left_bracket": 33,
    "i": 34,
    "p": 35,
    "return": 36,
    "l": 37,
    "j": 38,
    "quote": 39,
    "k": 40,
    "semicolon": 41,
    "backslash": 42,
    "comma": 43,
    "slash": 44,
    "n": 45,
    "m": 46,
    "period": 47,
    "tab": 48,
    "space": 49,
    "grave": 50,
    "delete": 51,
    "escape": 53,
    "command": 55,
    "shift": 56,
    "caps_lock": 57,
    "option": 58,
    "control": 59,
    "right_shift": 60,
    "right_option": 61,
    "right_control": 62,
    "function": 63,
    "f17": 64,
    "keypad_decimal": 65,
    "keypad_multiply": 67,
    "keypad_plus": 69,
    "keypad_clear": 71,
    "volume_up": 72,
    "volume_down": 73,
    "mute": 74,
    "keypad_divide": 75,
    "keypad_enter": 76,
    "keypad_minus": 78,
    "f18": 79,
    "f19": 80,
    "keypad_equals": 81,
    "keypad_0": 82,
    "keypad_1": 83,
    "keypad_2": 84,
    "keypad_3": 85,
    "keypad_4": 86,
    "keypad_5": 87,
    "keypad_6": 88,
    "keypad_7": 89,
    "f20": 90,
    "keypad_8": 91,
    "keypad_9": 92,
    "f5": 96,
    "f6": 97,
    "f7": 98,
    "f3": 99,
    "f8": 100,
    "f9": 101,
    "f11": 103,
    "f13": 105,
    "f16": 106,
    "f14": 107,
    "f10": 109,
    "f12": 111,
    "f15": 113,
    "help": 114,
    "home": 115,
    "page_up": 116,
    "forward_delete": 117,
    "f4": 118,
    "end": 119,
    "f2": 120,
    "page_down": 121,
    "f1": 122,
    "left_arrow": 123,
    "right_arrow": 124,
    "down_arrow": 125,
    "up_arrow": 126,
}

WINDOWS_FORMAT = (
    "%{app-name} %{window-title} %{window-id} %{app-pid} "
    "%{workspace} %{app-bundle-id} %{monitor-name}"
)

_app_path_cache: Dict[str, Optional[str]] = {}


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
        with open(path, "rb") as handle:
            config = tomllib.load(handle)
    except Exception as exc:  # pylint: disable=broad-except
        return {"error": f"Failed to parse config: {exc}", "path": path}

    return {"config": config, "path": path}


def normalize_description(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=True)
    text = text.replace('"', "")
    return re.sub(r"(?<=\w)-(?=\w)", " ", text)


def extract_shortcuts(config: Dict[str, Any]) -> List[Dict[str, str]]:
    shortcuts: List[Dict[str, str]] = []
    modes = config.get("mode", {})
    if not isinstance(modes, dict):
        return shortcuts

    for mode_name, mode_config in modes.items():
        if not isinstance(mode_config, dict):
            continue
        bindings = mode_config.get("binding", {})
        if not isinstance(bindings, dict):
            continue
        for shortcut, command in bindings.items():
            shortcuts.append(
                {
                    "mode": str(mode_name),
                    "shortcut": str(shortcut),
                    "description": normalize_description(command),
                }
            )
    return shortcuts


def parse_shortcut(shortcut: str) -> tuple[List[str], str]:
    parts = [part for part in shortcut.split("-") if part]
    if not parts:
        return [], ""
    return parts[:-1], parts[-1]


def _escape_applescript(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', "\\\"")


def build_applescript(shortcut: str) -> str:
    modifiers, key = parse_shortcut(shortcut)
    modifier_tokens = [
        MODIFIER_MAP[mod]
        for mod in modifiers
        if mod in MODIFIER_MAP
    ]
    keycode = KEYCODE_MAP.get(key.lower())
    if keycode is not None:
        action = f"key code {keycode}"
    else:
        action = f'keystroke "{_escape_applescript(key)}"'

    if modifier_tokens:
        action = f"{action} using {{{', '.join(modifier_tokens)}}}"

    modifier_label = " ".join(modifiers) if modifiers else "none"
    return (
        "tell application \"System Events\"\n"
        f"    {action}\n"
        f"    return \"Executed: {shortcut}({modifier_label} - {key})\"\n"
        "end tell"
    )


def run_applescript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or "AppleScript failed.")
    return result.stdout.strip()


def execute_shortcut(shortcut: str) -> str:
    script = build_applescript(shortcut)
    return run_applescript(script)


def get_app_path(bundle_id: str) -> Optional[str]:
    if not bundle_id:
        return None
    if bundle_id in _app_path_cache:
        return _app_path_cache[bundle_id]

    try:
        output = _run_command(
            [
                "mdfind",
                f'kMDItemCFBundleIdentifier="{bundle_id}"',
            ]
        ).strip()
    except Exception:  # pylint: disable=broad-except
        output = ""

    app_path = output.splitlines()[0] if output else None
    _app_path_cache[bundle_id] = app_path
    return app_path


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

    output = _run_command(args)
    windows = json.loads(output)
    if not isinstance(windows, list):
        return []

    for window in windows:
        bundle_id = window.get("app-bundle-id")
        if isinstance(bundle_id, str):
            window["app-path"] = get_app_path(bundle_id)
    return windows


def focus_window(window_id: str) -> None:
    _run_command(["aerospace", "focus", "--window-id", str(window_id)])
