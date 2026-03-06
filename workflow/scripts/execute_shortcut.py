#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import (
    display_notification,
    notify_error,
    run_aerospace_command,
    trigger_binding,
)


def _execute_action(action: str) -> str:
    payload = json.loads(action)
    if not isinstance(payload, dict):
        raise RuntimeError("Expected Alfred payload object.")
    action_type = str(payload.get("type", "")).strip().lower()
    if action_type == "binding":
        binding = str(payload.get("binding", "")).strip()
        mode = str(payload.get("mode", "")).strip()
        output = trigger_binding(binding, mode)
        return output or f"Triggered: {binding} (mode: {mode})"
    if action_type == "command":
        command = str(payload.get("command", "")).strip()
        output = run_aerospace_command(command)
        return output or f"Executed: aerospace {command}"

    raise RuntimeError(f"Unsupported Alfred action type: {action_type or 'missing'}")


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if not action:
        action = sys.stdin.read().strip()
    if not action:
        return
    notifications = os.environ.get("ENABLE_NOTIFICATIONS", "true").strip().lower()
    notifications_enabled = notifications in {"1", "true", "yes", "on"}
    try:
        output = _execute_action(action)
    except Exception as exc:  # pylint: disable=broad-except
        notify_error(str(exc))
        print(str(exc))
        raise SystemExit(1) from exc
    if output:
        print(output)
        if notifications_enabled:
            display_notification(output)


if __name__ == "__main__":
    main()
