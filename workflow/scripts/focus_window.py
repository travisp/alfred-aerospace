#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import focus_window


def main() -> None:
    window_id = sys.argv[1] if len(sys.argv) > 1 else ""
    if not window_id:
        window_id = sys.stdin.read().strip()
    if not window_id:
        return
    try:
        focus_window(window_id)
    except Exception as exc:  # pylint: disable=broad-except
        print(str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
