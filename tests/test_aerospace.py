import json
import subprocess
import sys
import textwrap
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflow" / "scripts"))

from lib.aerospace import extract_shortcuts, get_focused_window, list_windows


CONFIG_TEXT = textwrap.dedent(
    """
    start-at-login = true

    [mode.main.binding]
    alt-c = 'exec-and-forget open -a ChatGPT'
    alt-b = ['balance-sizes', 'mode main']
    # alfred-name: Should Not Apply
    alt-i = 'workspace Inbox'
    alt-f = 'flatten-workspace-tree' # alfred-name: Flatten Tree
    alt-s = 'workspace Secret' # alfred-skip
    alt-q = '''
    exec-and-forget bash -lc "echo hidden"
    ''' # alfred-skip

    [mode."service-mode".binding]
    "alt-shift-h" = ['join-with left', 'mode main']
    alt-shift-f = '''exec-and-forget bash -lc '
    echo fix
    ' ''' # alfred-name: Fix Layout

    [mode.main]
    # alfred-name: Should not leak
    """
)


class ExtractShortcutsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = tomllib.loads(CONFIG_TEXT)

    def test_uses_inline_alfred_name_comments_for_display_names(self) -> None:
        shortcuts = extract_shortcuts(self.config, CONFIG_TEXT)
        entries = {
            (shortcut["mode"], shortcut["shortcut"]): shortcut for shortcut in shortcuts
        }

        self.assertEqual(entries[("main", "alt-f")]["description"], "Flatten Tree")
        self.assertEqual(
            entries[("service-mode", "alt-shift-f")]["description"], "Fix Layout"
        )

    def test_preserves_existing_fallback_description_without_inline_comment(
        self,
    ) -> None:
        shortcuts = extract_shortcuts(self.config, CONFIG_TEXT)
        entries = {
            (shortcut["mode"], shortcut["shortcut"]): shortcut for shortcut in shortcuts
        }

        self.assertEqual(entries[("main", "alt-b")]["description"], "balance-sizes")
        self.assertEqual(
            entries[("main", "alt-c")]["description"],
            "exec and forget open -a ChatGPT",
        )
        self.assertEqual(entries[("main", "alt-i")]["description"], "workspace Inbox")
        self.assertEqual(
            entries[("service-mode", "alt-shift-h")]["description"],
            "join-with left",
        )
        self.assertIn(
            "exec and forget open -a ChatGPT",
            entries[("main", "alt-c")]["command"],
        )

    def test_skips_bindings_marked_with_alfred_skip(self) -> None:
        shortcuts = extract_shortcuts(self.config, CONFIG_TEXT)
        entries = {
            (shortcut["mode"], shortcut["shortcut"]): shortcut for shortcut in shortcuts
        }

        self.assertNotIn(("main", "alt-s"), entries)
        self.assertNotIn(("main", "alt-q"), entries)


class WindowAppPathTest(unittest.TestCase):
    def test_batches_unique_pids_and_matches_paths_by_pid(self) -> None:
        windows = [
            {"app-pid": 101},
            {"app-pid": 102},
            {"app-pid": 101},
            {"app-pid": 103},  # Exited between the window list and the lookup.
            {"app-pid": 104},  # Still running but has no bundle path.
        ]
        # Captured from chained lsappinfo queries, with PIDs normalized and a null-path record added.
        output = (
            '[ NULL ]  ASN:0x0-0x1f01f: \n'
            '    bundleID=[ NULL ] \n'
            '    bundle path="/System/Applications/Messages.app"\n'
            '    executable path=[ NULL ] \n'
            '    pid = 102 !cgsConnection !signalled type=[ NULL ]  flavor=[ NULL ]  Version=[ NULL ]  Arch=!!none \n\n'
            '[ NULL ]  ASN:0x0-0x404: \n'
            '    bundleID=[ NULL ] \n'
            '    bundle path=[ NULL ] \n'
            '    executable path=[ NULL ] \n'
            '    pid = 104 !cgsConnection !signalled type=[ NULL ]  flavor=[ NULL ]  Version=[ NULL ]  Arch=!!none \n\n'
            '[ NULL ]  ASN:0x0-0x1d01d: \n'
            '    bundleID=[ NULL ] \n'
            '    bundle path="/Applications/Ghostty.app"\n'
            '    executable path=[ NULL ] \n'
            '    pid = 101 !cgsConnection !signalled type=[ NULL ]  flavor=[ NULL ]  Version=[ NULL ]  Arch=!!none \n\n'
        )
        with patch(
            "lib.aerospace._run_command", side_effect=[json.dumps(windows), output]
        ) as run:
            result = list_windows("all")

        self.assertEqual(
            [window.get("app-path") for window in result],
            [
                "/Applications/Ghostty.app",
                "/System/Applications/Messages.app",
                "/Applications/Ghostty.app",
                None,
                None,
            ],
        )
        self.assertEqual(run.call_count, 2)
        args = run.call_args.args[0]
        self.assertEqual(args[0], "/usr/bin/lsappinfo")
        self.assertCountEqual(
            [args[i:i + 4] for i in range(1, len(args), 4)],
            [["info", "-only", "pid,bundlepath", pid] for pid in ("101", "102", "103", "104")],
        )

    def test_focused_window_resolves_app_path(self) -> None:
        window = {"window-id": 1, "app-pid": 101}
        output = (
            '[ NULL ]  ASN:0x0-0x101: (in front)\n'
            '    bundle path="/Applications/Editor.app"\n'
            '    pid = 101\n'
        )
        with patch(
            "lib.aerospace._run_command", side_effect=[json.dumps([window]), output]
        ) as run:
            result = get_focused_window()

        self.assertEqual(result, {**window, "app-path": "/Applications/Editor.app"})
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0][-1], "101")

    def test_icon_lookup_failure_does_not_hide_windows(self) -> None:
        window = {"window-id": 1, "app-pid": 101}
        for failure in (
            FileNotFoundError("lsappinfo"),
            RuntimeError("lsappinfo failed"),
            subprocess.TimeoutExpired("lsappinfo", 1),
        ):
            with self.subTest(error=type(failure).__name__), patch(
                "lib.aerospace._run_command", side_effect=[json.dumps([window]), failure]
            ):
                self.assertEqual(list_windows("all"), [window])

    def test_skips_app_lookup_when_no_windows_are_returned(self) -> None:
        with patch("lib.aerospace._run_command", return_value="[]") as run:
            self.assertEqual(list_windows("all"), [])
            run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
