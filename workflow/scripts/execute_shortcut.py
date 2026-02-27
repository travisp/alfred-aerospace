#!/usr/bin/env python3

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import display_notification, execute_shortcut, run_aerospace_command


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if not action:
        action = sys.stdin.read().strip()
    if not action:
        return
    notifications = os.environ.get("ENABLE_NOTIFICATIONS", "true").strip().lower()
    notifications_enabled = notifications in {"1", "true", "yes", "on"}
    try:
        if action.startswith("command:"):
            command = action[len("command:") :].strip()
            output = run_aerospace_command(command)
            if not output:
                output = f"Executed: aerospace {command}"
        else:
            output = execute_shortcut(action)
    except Exception as exc:  # pylint: disable=broad-except
        print(str(exc))
        raise SystemExit(1) from exc
    if output:
        print(output)
        if notifications_enabled:
            display_notification(output)


if __name__ == "__main__":
    main()
