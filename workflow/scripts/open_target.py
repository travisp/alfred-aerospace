#!/usr/bin/env python3

import subprocess
import sys


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    if not target:
        target = sys.stdin.read().strip()
    if not target:
        return
    subprocess.run(["open", target], check=False)


if __name__ == "__main__":
    main()
