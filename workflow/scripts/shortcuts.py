#!/usr/bin/env python3

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import extract_shortcuts, load_config


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if not query:
        query = sys.stdin.read().strip()

    result = load_config()
    if "error" in result:
        items = [
            {
                "title": "AeroSpace config error",
                "subtitle": result["error"],
                "valid": False,
            }
        ]
        print(json.dumps({"items": items}))
        return

    shortcuts = extract_shortcuts(result["config"])
    items = []
    query_lower = query.lower()
    for shortcut in shortcuts:
        title = shortcut["description"]
        subtitle = f"{shortcut['shortcut']} - mode: {shortcut['mode']}"
        match_text = f"{title} {shortcut['shortcut']} {shortcut['mode']}"
        if query_lower and query_lower not in match_text.lower():
            continue
        items.append(
            {
                "title": title,
                "subtitle": subtitle,
                "arg": shortcut["shortcut"],
                "uid": f"shortcut:{shortcut['mode']}:{shortcut['shortcut']}",
                "match": match_text,
            }
        )

    print(json.dumps({"items": items}))


if __name__ == "__main__":
    main()
