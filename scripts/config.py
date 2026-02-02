#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aerospace import INSTALL_GUIDE_URL, load_config


def _write_preview(path: str) -> str:
    cache_root = os.environ.get("alfred_workflow_cache") or "/tmp"
    preview_path = Path(cache_root) / "aerospace_config_preview.txt"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    preview_path.write_text(content, encoding="utf-8")
    return str(preview_path)


def main() -> None:
    result = load_config()
    if "error" in result:
        items = [
            {
                "title": "AeroSpace config unavailable",
                "subtitle": result["error"],
                "arg": INSTALL_GUIDE_URL,
                "valid": True,
            }
        ]
    else:
        path = result["path"]
        preview_path = path
        try:
            preview_path = _write_preview(path)
        except Exception:  # pylint: disable=broad-except
            preview_path = path
        items = [
            {
                "title": "AeroSpace Config",
                "subtitle": path,
                "arg": path,
                "quicklookurl": preview_path,
                "type": "file",
            }
        ]

    print(json.dumps({"items": items}))


if __name__ == "__main__":
    main()
