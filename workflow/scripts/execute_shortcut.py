#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import display_notification, execute_shortcut


def main() -> None:
    shortcut = sys.argv[1] if len(sys.argv) > 1 else ""
    if not shortcut:
        shortcut = sys.stdin.read().strip()
    if not shortcut:
        return
    try:
        output = execute_shortcut(shortcut)
    except Exception as exc:  # pylint: disable=broad-except
        print(str(exc))
        raise SystemExit(1) from exc
    if output:
        print(output)
        display_notification(output)


if __name__ == "__main__":
    main()
