#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import set_layout


def main() -> None:
    layout = sys.argv[1] if len(sys.argv) > 1 else ""
    if not layout:
        layout = sys.stdin.read().strip()
    if not layout:
        return
    try:
        set_layout(layout)
    except Exception as exc:  # pylint: disable=broad-except
        print(str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
